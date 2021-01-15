import json
import os
import platform
import tkinter as tk
import subprocess
from tkinter import scrolledtext as st
from tkinter import ttk
import api
import linux
import macos
import windows



class Workbench:

    def __init__(self, root):
        self.root = root
        self._frame = None
        f = open('config/config.json', 'r', encoding='utf-8')
        self.config = json.load(f)
        f.close()
        f = open('lang/lang.json', 'r', encoding='utf-8')
        self.lang = json.load(f)
        f.close()
        self.set_language()
        self.switch_frame("main_menu")
        self.version = "1.0.0"

    def set_language(self):
        if platform.system() == 'Windows':
            cmd = ['Get-WinSystemLocale | select Name | ConvertTo-JSON']
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    stdin=subprocess.PIPE)
            output, errors = proc.communicate()
            proc.wait()
            if proc.returncode >= 0:
                try:
                    lang = output.decode('utf-8')
                except:
                    lang = "en"

                if lang.find('es') != -1:
                    self.config['language'] = "ESP"
                elif lang.find('en') != -1:
                    self.config['language'] = "ENG"
                elif lang.find('cat') != -1:
                    self.config['language'] = "CAT"

        elif platform.system() == 'Linux':
            cmd = ['cat /etc/locale.conf']
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    stdin=subprocess.PIPE)
            output, errors = proc.communicate()
            proc.wait()
            if proc.returncode >= 0:
                try:
                    lang = output.decode('utf-8')
                except:
                    lang = "en"

                if lang.find('es') != -1:
                    self.config['language'] = "ESP"
                elif lang.find('en') != -1:
                    self.config['language'] = "ENG"
                elif lang.find('cat') != -1:
                    self.config['language'] = "CAT"
        else:
            cmd = ['osascript -e ''user locale of (get system info)''']
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    stdin=subprocess.PIPE)
            output, errors = proc.communicate()
            proc.wait()
            if proc.returncode >= 0:
                try:
                    lang = output.decode('utf-8')
                except:
                    lang = "en"

                if lang.find('es') != -1:
                    self.config['language'] = "ESP"
                elif lang.find('en') != -1:
                    self.config['language'] = "ENG"
                elif lang.find('cat') != -1:
                    self.config['language'] = "CAT"

    def switch_frame(self, frame_class):
        if self._frame is not None:
            self._frame.destroy()
        if frame_class == "main_menu":
            self.main_menu()
        elif frame_class == "consent_page":
            self.consent_page()
        elif frame_class == "snapshot_progress":
            self.snapshot_progress()
        elif frame_class == "view_json":
            self.view_json()
        elif frame_class == "settings":
            self.settings()
        elif frame_class == "final_page":
            result = self.send_snapshot()
            self.final_page(result)

    def do_snapshot(self):
        if platform.system() == 'Windows':
            machine = windows.Windows()
        elif platform.system() == 'Linux':
            machine = linux.Linux()
        elif platform.system() == 'Darwin':
            machine = macos.MacOS()

        self.snapshot = machine.do_snapshot(self.version)

        if self._frame is not None:
            self._frame.destroy()
        self.consent_page()

    def send_snapshot(self):

        result = api.send_snapshot(self.config["domain"], self.snapshot)
        return result

    def get_license(self):
        license = api.get_license(self.config["domain"], self.version, self.config["language"])
        if type(license) == str:
            if self._frame is not None:
                self._frame.destroy()
            self.final_page(-1)
        else:
            self.license_version = license["USOdyPrivacyPolicyVersion"]
            return license["Description"]

    def save_settings(self):
        self.config["language"] = self.language_combobox.get()
        self.config["domain"] = self.url_entry.get()
        with open('config/config.json', 'w', encoding='utf-8') as outfile:
            json.dump(self.config, outfile)
        self.switch_frame("main_menu")

    def switch_button_agreement(self):
        if self.agreement is True:
            self.button_submit_menu = tk.Button(self._frame,
                                        font=('Arial Bold', 12), width=20, height=1,
                                        state=tk.DISABLED,
                                        text=self.lang["consent_menu"]["submit_button"][self.config["language"]])
            self.button_submit_menu.grid(row=4, column=0)
            self.agreement = False
        else:
            self.button_submit_menu = tk.Button(self._frame, font=('Arial Bold', 12),
                                        width=20, height=1, state=tk.NORMAL,
                                        command=lambda: self.switch_frame("final_page"),
                                        text=self.lang["consent_menu"]["submit_button"][self.config["language"]])
            self.button_submit_menu.grid(row=4, column=0)
            self.agreement = True

    def main_menu(self):
        self._frame = tk.Frame(self.root)
        self._frame.place(relx=0.5, rely=0.4, anchor=tk.CENTER)

        self.title_menu = tk.Label(self._frame, font=('Arial Bold', 26, 'underline'), text="Workbench Desktop")

        self.button_snapshot = tk.Button(self._frame, font=('Arial Bold', 12),
                                         command=lambda: self.switch_frame("snapshot_progress"),
                                         width=50, height=2,
                                         text=self.lang["main_menu"]["snapshot_button"][self.config["language"]])

        self.button_settings = tk.Button(self._frame, font=('Arial Bold', 12),
                                         command=lambda: self.switch_frame("settings"),
                                         width=50, height=2,
                                         text=self.lang["main_menu"]["settings_button"][self.config["language"]])

        self.button_quit = tk.Button(self._frame, font=('Arial Bold', 12), command=main_win.quit,
                                     width=50, height=2,
                                     text=self.lang["general"]["exit_button"][self.config["language"]])

        self.title_menu.grid(row=0, column=0, pady=(0, 40))
        self.button_snapshot.grid(row=1, column=0, pady=(0, 20))
        self.button_settings.grid(row=2, column=0, pady=(0, 20))
        self.button_quit.grid(row=3, column=0, pady=(0, 20))

    def view_json(self):
        json_pretty = json.dumps(self.snapshot, indent=2)

        self._frame = tk.Frame(self.root)
        self._frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.title_view_json = tk.Label(self._frame, font=('Arial Bold', 20, 'underline'),
                                    text=self.lang["consent_menu"]["title_view_json"][self.config["language"]])

        self.text_area = st.ScrolledText(self._frame, width=80, height=24, font=("Arial", 12))
        self.text_area.grid(row=1, column=0, pady=20)
        self.text_area.tag_config('justify', justify=tk.LEFT)
        self.text_area.insert(tk.INSERT, json_pretty, "justify")
        self.text_area.configure(state='disabled')
        self.button_view_json = tk.Button(self._frame, font=('Arial Bold', 12),
                                    width=20, height=1, command=lambda: self.switch_frame("consent_page"),
                                    text=self.lang["general"]["back_button"][self.config["language"]])

        self.title_view_json.grid(row=0, column=0, pady=20)
        self.button_view_json.grid(row=2, column=0)

    def settings(self):
        self._frame = tk.Frame(self.root)
        self._frame.place(relx=0.5, rely=0.4, anchor=tk.CENTER)
        self.title_settings = tk.Label(self._frame, font=('Arial Bold', 26, 'underline'),
                                       text=self.lang["settings_menu"]["settings_title"][self.config["language"]])

        self.language_label = tk.Label(self._frame, font=('Arial Bold', 12),
                                       text=self.lang["settings_menu"]["language_label"][self.config["language"]])

        self.language_combobox = ttk.Combobox(self._frame, state="readonly", font=('Arial Bold', 12))
        self.language_combobox["values"] = ["ENG", "ESP", "CAT"]
        self.language_combobox.set(self.config["language"])

        self.url_label = tk.Label(self._frame, font=('Arial Bold', 12),
                                  text=self.lang["settings_menu"]["url_label"][self.config["language"]])

        self.url_entry = ttk.Entry(self._frame, font=('Arial Bold', 12), width=35)
        self.url_entry.insert(tk.END, self.config["domain"])

        self.button_save_settings = tk.Button(self._frame, font=('Arial Bold', 12),
                                              command=self.save_settings, width=30, height=2,
                                              text=self.lang["settings_menu"]["save_button"][self.config["language"]])

        self.button_back_menu = tk.Button(self._frame, font=('Arial Bold', 12),
                                          command=lambda: self.switch_frame("main_menu"), width=30, height=2,
                                          text=self.lang["general"]["back_button"][self.config["language"]])

        self.title_settings.grid(row=0, column=2, columnspan=2, padx=(0, 300))
        self.language_label.grid(row=1, column=0, pady=(40, 0))
        self.language_combobox.grid(row=1, column=3, pady=(40, 0))
        self.url_label.grid(row=2, column=0, pady=(40, 0))
        self.url_entry.grid(row=2, column=3, pady=(40, 0))
        self.button_save_settings.grid(row=3, column=0, pady=(40, 0))
        self.button_back_menu.grid(row=3, column=3, pady=(40, 0))


    def consent_page(self):

        license = self.get_license()
        self.snapshot["licence_version"] = self.license_version

        self._frame = tk.Frame(self.root)
        self._frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.title_consent = tk.Label(self._frame, font=('Arial Bold', 20, 'underline'),
                                      text=self.lang["consent_menu"]["title_consent"][self.config["language"]])

        self.text_area = st.ScrolledText(self._frame, width=80, height=18, font=("Arial", 12))

        self.text_area.tag_config('justify', justify=tk.LEFT)
        self.text_area.insert(tk.INSERT, license, "justify")
        self.text_area.configure(state='disabled')

        self.button_view_json = tk.Button(self._frame, font=('Arial Bold', 12),width=20, height=1,
                                      command=lambda: self.switch_frame("view_json"),
                                      text=self.lang["consent_menu"]["view_json_button"][self.config["language"]])

        self.checkbox_agreement = tk.Checkbutton(self._frame, font=('Arial Bold', 12),
                                         command=self.switch_button_agreement,
                                         text=self.lang["consent_menu"]["checkbox_consent"][self.config["language"]])

        self.button_submit_menu = tk.Button(self._frame, font=('Arial Bold', 12),
                                         width=20, height=1, state=tk.DISABLED,
                                         text=self.lang["consent_menu"]["submit_button"][self.config["language"]])

        self.agreement = False

        self.title_consent.grid(row=0, column=0, pady=20)
        self.text_area.grid(row=1, column=0, pady=20)
        self.button_view_json.grid(row=2, column=0)
        self.checkbox_agreement.deselect()
        self.checkbox_agreement.grid(row=3, column=0, pady=20)
        self.button_submit_menu.grid(row=4, column=0)

    def snapshot_progress(self):

        self._frame = tk.Frame(self.root)
        self._frame.place(relx=0.5, rely=0.45, anchor=tk.CENTER)

        self.title_working = tk.Label(self._frame,font=('Arial Bold', 20),
                                      text=self.lang["progress_menu"]["title_working"][self.config["language"]])
        self.title_reusing = tk.Label(self._frame,
                                      text=self.lang["progress_menu"]["title_reusing"][self.config["language"]],
                                      font=('Arial Bold', 20))
        self.title_time = tk.Label(self._frame,
                                   text=self.lang["progress_menu"]["title_time"][self.config["language"]],
                                   font=('Arial Bold', 20))

        self.title_working.grid(row=0, column=0, pady=40,)
        self.title_reusing.grid(row=1, column=0, pady=30)
        self.title_time.grid(row=2, column=0, pady=30)

        self.root.update()
        self.do_snapshot()

    def final_page(self, result):
        self._frame = tk.Frame(self.root)
        self._frame.place(relx=0.5, rely=0.4, anchor=tk.CENTER)
        self.title_result = tk.Label(self._frame, font=('Arial Bold', 26, 'underline'))
        self.button_quit = tk.Button(self._frame, font=('Arial Bold', 12), command=main_win.quit,
                                     width=50, height=2,
                                     text=self.lang["general"]["exit_button"][self.config["language"]])

        if result < 0:
            self.title_result["text"] = self.lang["final_menu"]["upload_final_fail"][self.config["language"]]
        else:
            self.title_result["text"] = self.lang["final_menu"]["upload_final_ok"][self.config["language"]]

        self.thank_label = tk.Label(self._frame, font=('Arial Bold', 26, 'underline'))

        if result < 0:
            self.thank_label["text"] = self.lang["final_menu"]["try_final_fail"][self.config["language"]]
            self.button_retry = tk.Button(self._frame, font=('Arial Bold', 12), command=lambda: self.switch_frame("main_menu"),
                                         width=50, height=2,
                                         text=self.lang["general"]["retry"][self.config["language"]])
            self.button_retry.grid(row=2, column=0, pady=(0, 20))
            self.button_quit.grid(row=3, column=0, pady=(0, 20))
        else:
            self.thank_label["text"] = self.lang["final_menu"]["thank_final_ok"][self.config["language"]]
            self.button_quit.grid(row=2, column=0, pady=(0, 20))

        self.title_result.grid(row=0, column=0, pady=(0, 40))
        self.thank_label.grid(row=1, column=0, pady=(0, 40))


if __name__ == "__main__":
    main_win = tk.Tk()
    file_to_open = os.path.join(os.getcwd(), "img/logo.ico")
    try:
        main_win.iconbitmap(file_to_open)
    except:
        main_win.call('wm', 'iconphoto', main_win._w, tk.PhotoImage(file_to_open))
    main_win.title("eReuse.org")
    windowWidth = 1080
    windowHeight = 720

    x_coordinate = int(main_win.winfo_screenwidth() / 2 - windowWidth / 2)
    y_coordinate = int(main_win.winfo_screenheight() / 2 - windowHeight / 2)

    main_win.geometry("%dx%d+%d+%d" % (windowWidth, windowHeight, x_coordinate, y_coordinate))

    main_win.resizable(width=False, height=False)

    app = Workbench(main_win)
    main_win.mainloop()
