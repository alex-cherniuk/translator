#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    from tkinter import Tk, Frame, Menu, Text, Label, Scrollbar, filedialog
    from tkinter.messagebox import askyesno, showerror
    from tkinter.ttk import Notebook, Button
except ImportError:
    raise ImportError('Try to use python 3')
import os
from file_wrapper import FileWrapper, CSVWrapper
from compiler import Compiler

NORMAL_FONT = ("Verdana", 10)
PYTHON_FONT = ("Courier New", 9)

file_types = {"All Files": "*.*", "Plain Text": "*.txt"}
file_types_list = [[key, value] for key, value in file_types.items()]


class CompilerGUI(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.iconbitmap(default="Rocket.ico")
        self.geometry("800x600")
        self.set_title()
        self.container = Container(self)
        self.container.pack(side='top', fill='x', expand=False)
        self.mainframe = MainFrame(self)
        self.mainframe.pack(side="top", fill="both", expand=True)
        self.init_keystrokes()
        self.status_bar = StatusBar(self)
        self.status_bar.pack(side="bottom", fill="x", padx=5, pady=5)
        self.console = ConsolePanel(self)

    def init_keystrokes(self):
        for key in ["<Control-n>", "<Control-N>"]:
            self.bind(key, self.new_file)
        for key in ["<Control-o>", "<Control-O>"]:
            self.bind(key, self.open_file)
        for key in ["<Control-s>", "<Control-S>"]:
            self.bind(key, self.save_file)
        for key in ["<Control-Shift-s>", "<Control-Shift-S>"]:
            self.bind(key, self.save_file_as)
        for key in ["<Control-w>", "<Control-W>"]:
            self.bind(key, self.close_file)
        for key in ["<Control-b>", "<Control-B>"]:
            self.bind(key, self.container.tool_bar.run)

    def set_title(self, file_path=""):
        if file_path:
            self.wm_title(file_path + " - " + "Rocket Compiler")
        else:
            self.wm_title("Rocket Compiler")

    def update_title(self):
        if self.mainframe.frames:
            tab_id = self.mainframe.index('current')
            self.set_title(self.mainframe.frames[tab_id].file.file_path)
        else:
            self.set_title()

    def new_file(self, _):
        self.mainframe.add_tab(NotebookTab(self.mainframe, FileWrapper("Untitled")))

    @staticmethod
    def ask_open_file_path():
        global file_types_list
        return filedialog.askopenfilename(initialdir="/", title="Open File", filetypes=file_types_list)

    @staticmethod
    def ask_save_file_path():
        global file_types_list
        return filedialog.asksaveasfilename(initialdir="/", title="Save File", filetypes=file_types_list)

    def open_file(self, _):
        file_path = self.ask_open_file_path()
        if file_path:
            if file_path in self.mainframe.used_file_paths:
                tab_id = self.mainframe.used_file_paths.index(file_path)
                self.mainframe.show_tab(tab_id)
            else:
                self.mainframe.add_tab(NotebookTab(self.mainframe, FileWrapper(file_path)))

    def save_file(self, _, tab_id=None):
        if self.mainframe.frames:
            if not tab_id:
                tab_id = self.mainframe.index('current')
            file_path = self.mainframe.frames[tab_id].file.file_path
            if file_path == "Untitled":
                self.save_file_as(True, tab_id=tab_id)
            else:
                FileWrapper.write_file(file_path=file_path, text=self.mainframe.frames[tab_id].text)
                self.mainframe.frames[tab_id].file.changed = False

    def save_file_as(self, _, tab_id=None):
        if self.mainframe.frames:
            new_file_path = self.ask_save_file_path()
            if new_file_path:
                if not tab_id:
                    tab_id = self.mainframe.index('current')
                self.mainframe.frames[tab_id].file.file_path = new_file_path
                FileWrapper.write_file(file_path=new_file_path, text=self.mainframe.frames[tab_id].text)
                self.mainframe.frames[tab_id].file.changed = False
                self.mainframe.update_tab(tab_id)

    def close_file(self, _, tab_id=None):
        if self.mainframe.frames:
            if not tab_id:
                tab_id = self.mainframe.index('current')
            # ask about saving
            if self.mainframe.frames[tab_id].file.changed:
                filename = self.mainframe.frames[tab_id].file.filename
                answer = askyesno("Save the changes?", f"{filename} has been modified. Save the changes?")
                if answer:
                    self.save_file(True, tab_id=tab_id)
            self.mainframe.remove_tab(tab_id)
            self.update_title()

    def close_all_files(self):
        number_of_tabs = len(self.mainframe.frames)
        for tab_id in range(number_of_tabs):
            self.close_file(True, tab_id=number_of_tabs-(tab_id+1))

    def check_and_save(self, file, tab_id):
        if file.changed or file.file_path == 'Untitled':
            answer = askyesno("Save the changes?",
                              f"File {file.filename} has been modified (not saved). Save and continue?")
            if answer:
                self.save_file(True, tab_id=tab_id)
            return answer
        return True

    @staticmethod
    def show_info(info):
        info_path = os.getcwd().replace('\\', '/') + f'/info/{info}.txt'
        if os.path.isfile(info_path):
            if info == 'about':
                PopupMessage(FileWrapper.read_file(info_path), "About Compiler", "650x150").mainloop()
            elif info == 'grammar':
                PopupMessage(FileWrapper.read_file(info_path), "Grammar", "900x650", anchor='nw').mainloop()
            elif info == 'terminal lexemes':
                PopupMessage(FileWrapper.read_file(info_path), "Grammar", "300x650", anchor='n').mainloop()
        else:
            showerror("Error", f"File '../info/{info}.txt' does not exist.")


class TableWindow(Tk):
    def __init__(self, table_type, file_path, window_size="600x400"):
        Tk.__init__(self)
        self.table_type = table_type
        self.file_path = file_path
        self.csvfile = CSVWrapper(self.file_path)
        self.geometry(window_size)
        self.wm_title(self.title)
        ScrolledText(self, self.csvfile.text).pack(side='top', fill='both', expand=True)

    @property
    def filename(self):
        return self.file_path.split('/')[-1]

    @property
    def title(self):
        return "Table of {} ({}) - Rocket Compiler".format(self.table_type, self.filename)


class PopupMessage(Tk):
    def __init__(self, message, title, window_size="650x150", anchor='center'):
        Tk.__init__(self)
        self.wm_title(title)
        self.message = message
        self.geometry(window_size)
        for line in message.split('\n'):
            Label(self, text=line, font=PYTHON_FONT, anchor=anchor).pack(fill="both", padx=10, expand=False)
        self.button = Button(self, text="OK", command=self.destroy)
        self.button.pack(expand=True)


class ScrolledText(Frame):
    def __init__(self, parent, source_text=None):
        Frame.__init__(self, parent)
        self.parent = parent
        self.source_text = source_text

        # adding the text field
        self.filetext = Text(self, undo=True, autoseparators=True, maxundo=-1)
        if self.source_text:
            self.put_text(self.source_text)
        self.filetext.pack(side="left", fill="both", padx=5, expand=True)

        # adding the vertical scrollbar and connecting it with the text field
        self.vertical_scrollbar = Scrollbar(self, orient="vertical", command=self.filetext.yview)
        self.vertical_scrollbar.pack(side="right", fill="y")
        self.filetext.configure(yscrollcommand=self.vertical_scrollbar.set)

    def get_all_text(self):
        return self.filetext.get("1.0", "end-1c")

    def put_text(self, text):
        self.filetext.insert("end", text)

    def clear(self):
        self.filetext.delete("1.0", "end")

    @property
    def text(self):
        return self.get_all_text()

    @property
    def rows(self):
        return self.text.split('\n')

    @property
    def number_of_rows(self):
        return len(self.rows)


class MenuBar(Frame):
    def __init__(self, container):
        Frame.__init__(self, container)
        self.parent = container.parent
        self.menu_bar = Menu(self.parent)
        self.file_menu = Menu(self.menu_bar, tearoff=0)
        self.edit_menu = Menu(self.menu_bar, tearoff=0)
        self.view_menu = Menu(self.menu_bar, tearoff=0)
        self.tools_menu = Menu(self.menu_bar, tearoff=0)
        self.help_menu = Menu(self.menu_bar, tearoff=0)
        self.fill_file_menu()
        self.fill_edit_menu()
        self.fill_view_menu()
        self.fill_tools_menu()
        self.fill_help_menu()
        self.config_menu()

    def fill_file_menu(self):
        self.file_menu.add_command(label="New File                 Ctrl+N",
                                   command=lambda: self.parent.new_file(True))
        self.file_menu.add_command(label="Open File                Ctrl+O",
                                   command=lambda: self.parent.open_file(True))
        self.file_menu.add_command(label="Save File                  Ctrl+S",
                                   command=lambda: self.parent.save_file(True))
        self.file_menu.add_command(label="Save As ...     Ctrl+Shift+S",
                                   command=lambda: self.parent.save_file_as(True))
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Close File               Ctrl+W",
                                   command=lambda: self.parent.close_file(True))
        self.file_menu.add_command(label="Close All Files",
                                   command=lambda: self.parent.close_all_files())
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.quit)

    def fill_edit_menu(self):
        self.edit_menu.add_command(label="Undo                     Ctrl+Z",
                                   command=lambda: self.mainframe.text_command("undo"))
        self.edit_menu.add_command(label="Redo                      Ctrl+Y",
                                   command=lambda: self.mainframe.text_command("redo"))
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Copy                     Ctrl+C",
                                   command=lambda: self.mainframe.text_command("copy"))
        self.edit_menu.add_command(label="Cut                        Ctrl+X",
                                   command=lambda: self.mainframe.text_command("cut"))
        self.edit_menu.add_command(label="Paste                     Ctrl+V",
                                   command=lambda: self.mainframe.text_command("paste"))
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Select All               Ctrl+A",
                                   command=lambda: self.mainframe.text_command("select_all"))
        self.edit_menu.add_command(label="Deselect All",
                                   command=lambda: self.mainframe.text_command("deselect_all"))

    def fill_view_menu(self):
        self.view_menu.add_command(label="Show/Hide Console",
                                   command=lambda: self.console.show_or_hide())
        self.view_menu.add_command(label="Show/Hide Toolbar",
                                   command=lambda: self.tool_bar.show_or_hide())
        self.view_menu.add_command(label="Show Table of Lexemes",
                                   command=lambda: self.mainframe.show_table("lexemes"))
        self.view_menu.add_command(label="Show Table of Identifiers",
                                   command=lambda: self.mainframe.show_table("identifiers"))
        self.view_menu.add_command(label="Show Table of Constants",
                                   command=lambda: self.mainframe.show_table("constants"))
        self.view_menu.add_command(label="Show Table of Posfix History",
                                   command=lambda: self.mainframe.show_table("postfix_history"))
        self.view_menu.add_command(label="Show Table of Posfix Marks",
                                   command=lambda: self.mainframe.show_table("postfix_marks"))
        self.view_menu.add_command(label="Show Variables",
                                   command=lambda: self.mainframe.show_table("variables"))

    def fill_tools_menu(self):
        self.tools_menu.add_command(label="Lexical Analysis",
                                    command=lambda: self.tool_bar.lexical_analysis())
        self.tools_menu.add_command(label="Syntax Analysis",
                                    command=lambda: self.tool_bar.lexical_and_syntax_analysis())
        self.tools_menu.add_command(label="Postfix Notation",
                                    command=lambda: self.tool_bar.postfix())
        self.tools_menu.add_command(label="Run                        Ctrl+B",
                                    command=lambda: self.tool_bar.run(True))

    def fill_help_menu(self):
        self.help_menu.add_command(label="About Compiler", command=lambda: self.parent.show_info('about'))
        self.help_menu.add_command(label="Grammar", command=lambda: self.parent.show_info('grammar'))
        self.help_menu.add_command(label="Terminal Lexemes", command=lambda: self.parent.show_info('terminal lexemes'))

    def config_menu(self):
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)
        self.menu_bar.add_cascade(label="Tools", menu=self.tools_menu)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        self.parent.config(menu=self.menu_bar)

    @property
    def mainframe(self):
        return self.parent.mainframe

    @property
    def console(self):
        return self.parent.console

    @property
    def tool_bar(self):
        return self.parent.container.tool_bar


class ToolBar(Frame):
    def __init__(self, container):
        Frame.__init__(self, container)
        self.parent = container.parent
        self.packed = False
        self.button_lex = Button(self, text="LEX", command=lambda: self.lexical_analysis())
        self.button_syn = Button(self, text="SYN", command=lambda: self.lexical_and_syntax_analysis())
        self.button_pfix = Button(self, text="PFIX", command=lambda: self.postfix())
        self.button_run = Button(self, text="RUN", command=lambda: self.run(True))
        self.button_lex.pack(side="left")
        self.button_syn.pack(side="left")
        self.button_pfix.pack(side="left")
        self.button_run.pack(side="left")
        self.compiler = Compiler()

    @property
    def console(self):
        return self.parent.console

    @property
    def mainframe(self):
        return self.parent.mainframe

    def show_or_hide(self):
        if self.packed:
            self._hide()
        else:
            self._show(side='top', fill='x', pady=5)

    def _show(self, *args, **kwargs):
        self.pack(*args, **kwargs)
        self.packed = True

    def _hide(self):
        self.forget()
        self.packed = False

    def get_file(self):
        if self.mainframe.frames:
            tab_id = self.mainframe.index('current')
            file = self.mainframe.frames[tab_id].file
            isvalid = self.parent.check_and_save(file, tab_id)
            if not isvalid:
                return
            return file

    def lexical_analysis(self):
        file = self.get_file()
        if file:
            self.console.clear()
            self.compiler.get_lexemes(file, self.console.print_text, output_status=True)

    def lexical_and_syntax_analysis(self):
        file = self.get_file()
        if file:
            self.console.clear()
            self.compiler.get_match(file, self.console.print_text, output_status=True)

    def postfix(self):
        file = self.get_file()
        if file:
            self.console.clear()
            self.compiler.get_postfix(file, self.console.print_text, output_status=True)

    def run(self, _, value=None, start_position=0):
        file = self.get_file()
        if file:
            if value is None:
                self.console.clear()
            self.compiler.get_output(file, self.console.print_text, value, start_position)


class Container(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.parent = parent
        self.menu_bar = MenuBar(self)
        self.menu_bar.pack()
        self.tool_bar = ToolBar(self)


class MainFrame(Notebook):
    def __init__(self, parent):
        Notebook.__init__(self, parent)
        self.parent = parent
        self.frames = []
        self.bind('<ButtonRelease-1>', self.tab_changed)

    @property
    def used_file_paths(self):
        if self.frames:
            return [frame.file.file_path for frame in self.frames]
        return []

    def add_tab(self, frame):
        self.add(frame, text=frame.file.filename)
        self.frames.append(frame)
        self.show_tab(len(self.frames)-1)

    def show_tab(self, tab_id):
        self.select(self.frames[tab_id])
        self.parent.status_bar.update_bar(tab_id)
        self.parent.set_title(self.frames[tab_id].file.file_path)

    def update_tab(self, tab_id):
        self.tab(tab_id, text=self.frames[tab_id].file.filename)
        self.parent.set_title(self.frames[tab_id].file.file_path)

    def remove_tab(self, tab_id):
        self.forget(tab_id)
        self.frames = self.frames[:tab_id] + self.frames[tab_id+1:]
        self.parent.status_bar.update_bar()

    def tab_changed(self, _):
        if self.frames:
            tab_id = self.index('current')
            file_path = self.frames[tab_id].file.file_path
            self.parent.status_bar.update_bar(tab_id)
            self.parent.set_title(file_path)

    def show_table(self, table_type):
        if self.frames:
            tab_id = self.index('current')
            self.frames[tab_id].show_table(table_type=table_type)

    def text_command(self, command_type):
        if self.frames:
            eval("self.frames[self.index('current')]." + command_type + "(True)")


class ConsolePanel(ScrolledText):
    def __init__(self, parent):
        ScrolledText.__init__(self, parent)
        self.packed = False
        self.mode = 'output'
        self.input_text = None
        self.next_compiler_position = None
        self.filetext.bind("<Return>", self.get_input_text)

    def get_input_text(self, _):
        if self.mode == 'input':
            last_string = self.text.split('\n')[-1].strip()
            self.input_text = last_string[7:]
            try:
                value = float(self.input_text)
            except ValueError:
                self.put_text('\n' + 'Error! Value is not constant. Please try again.')
                self.print_text(mode='input')
            else:
                self.mode = 'output'
                self.tool_bar.run(_, value, self.next_compiler_position)

    def print_text(self, text='', mode='output', next_compiler_position=None):
        if not self.packed:
            self._show(side="bottom", fill="both", pady=5)
        if mode == 'output':
            self.put_text('\nOutput: ' + str(text))
        else:
            self.put_text('\n Input: ')
            self.mode = 'input'
            if next_compiler_position:
                self.next_compiler_position = next_compiler_position

    def show_or_hide(self):
        if self.packed:
            self._hide()
        else:
            self._show(side="bottom", fill="both", pady=5)

    def _show(self, *args, **kwargs):
        self.pack(*args, **kwargs)
        self.packed = True

    def _hide(self):
        self.forget()
        self.packed = False

    @property
    def tool_bar(self):
        return self.parent.container.tool_bar


class StatusBar(Label):
    def __init__(self, parent):
        Label.__init__(self, parent, anchor="w", text="")
        self.parent = parent

    def update_bar(self, tab_id=None):
        if self.parent.mainframe.frames:
            if tab_id or tab_id == 0:
                line, column = self.parent.mainframe.frames[tab_id].get_cursor_position()
            else:
                tab_id = self.parent.mainframe.index('current')
                line, column = self.parent.mainframe.frames[tab_id].get_cursor_position()
            self.config(text=f"Line {line}, Column {column}")
        else:
            self.config(text="")


class NotebookTab(ScrolledText):
    def __init__(self, mainframe, file):
        ScrolledText.__init__(self, mainframe, file.text)
        self.parent = mainframe.parent
        self.file = file
        self.context_menu = self.parent.container.menu_bar.edit_menu
        self.init_keystrokes()

    def init_keystrokes(self):
        for key in ["<Button-1>", "<Escape>"]:
            self.filetext.bind(key, self.deselect_all)
        self.filetext.bind('<ButtonRelease-3>', self.post_context_menu)
        self.filetext.bind('<ButtonRelease-1>', self.cursor_position_changed)
        self.filetext.bind('<KeyPress>', self.text_changed)

    def post_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)

    def copy(self, _):
        self.filetext.event_generate("<<Copy>>")

    def paste(self, event=None):
        self.filetext.event_generate("<<Paste>>")
        self.cursor_position_changed(event)
        self.file.changed = True

    def cut(self, event=None):
        self.filetext.event_generate("<<Cut>>")
        self.cursor_position_changed(event)
        self.file.changed = True

    def undo(self, event=None):
        self.filetext.event_generate("<<Undo>>")
        self.cursor_position_changed(event)
        self.file.changed = True

    def redo(self, event=None):
        self.filetext.event_generate("<<Redo>>")
        self.cursor_position_changed(event)
        self.file.changed = True

    def select_all(self, _):
        self.filetext.tag_add("sel", '1.0', 'end')

    def deselect_all(self, _):
        self.filetext.tag_remove("sel", '1.0', 'end')

    def text_changed(self, event):
        self.cursor_position_changed(event)
        self.file.changed = True

    def cursor_position_changed(self, _):
        self.parent.status_bar.update_bar()

    def get_cursor_position(self):
        return self.filetext.index('insert').split('.')

    def show_table(self, table_type):
        file_path = getattr(self.file, table_type+"_path")
        if os.path.isfile(file_path):
            TableWindow(table_type, file_path).mainloop()
        elif table_type in ['lexemes', 'identifiers', 'constants']:
            showerror("Error", "Lexical analysis for {} does not exist.".format(self.file.filename))
        elif table_type in ['postfix_history', 'postfix_marks']:
            showerror("Error", "Postfix notation for {} does not exist.".format(self.file.filename))
        elif table_type == 'variables':
            showerror("Error", "First run the programme!")


if __name__ == '__main__':
    CompilerGUI().mainloop()
