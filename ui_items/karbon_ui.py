import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import os
import re
import time
from pathlib import Path

from ui_items.prompt_view import PromptView
from ui_items.editor_view import EditorView, open_html_in_browser
from ui_items.token_manager_view import TokenManagerView
from contributors_page import ContributorsPage

from core.ai_engine import ai_status, generate_code_from_prompt
from exporters.exporter import export_code, export_to_github
from exporters.repo_pusher import push_to_github

EXAMPLES = {
    "Login Page": "Create a login page using HTML and Tailwind CSS",
    "Personal Portfolio Page": "Build a personal portfolio page with sections for About, Projects, and Contact",
    "Landing Page": "Design a landing page for a mobile app with a pricing section and testimonials",
    "Blog Homepage": "Create a dark-themed blog homepage with a navbar and featured articles",
    "Form": "Generate a simple form to collect name, email, and message with a submit button"
}


class KarbonUI:
    def __init__(self, root, active_user=None):
        self.root = root
        self.active_user = active_user
        print("KarbonUI started for:", self.active_user)

        self.setup_window()
        self.setup_styles()
        self.code = ""
        self.api_key = None
        self.model_source = None
        self.history = []  # To store prompt-output history


        self.main_container = tk.Frame(root, bg='#0d1117')
        self.main_container.pack(fill="both", expand=True)

        self.create_title_bar()

        # ✅✅ Add menubar and User menu
        self.menu_bar = tk.Menu(self.root)
        user_menu = tk.Menu(self.menu_bar, tearoff=0)
        user_menu.add_command(label="Switch User", command=self.switch_user)
        self.menu_bar.add_cascade(label="User", menu=user_menu)
        self.root.config(menu=self.menu_bar)

        self.paned_window = ttk.PanedWindow(self.main_container, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.prompt_view = PromptView(
            self.paned_window,
            on_generate=self.handle_prompt_generated,
            get_api_key_callback=self.get_api_key,
            get_model_source_callback=self.get_model_source,
            examples_data=EXAMPLES
        )
        self.editor_view = EditorView(
            self.paned_window,
            get_code_callback=self.get_code,
            set_code_callback=self.set_code,
            get_api_key_callback=self.get_api_key,
            get_model_source_callback=self.get_model_source
        )

    # View History Button
        self.history_button = tk.Button(
              self.main_container, text="View History", command=self.show_history_panel)
        self.history_button.pack(pady=(0, 10))


        self.load_settings()

        self.example_var = tk.StringVar(value="🔽 Choose Example Prompt")
        PADDED_EXAMPLES = {key.ljust(30): prompt for key, prompt in EXAMPLES.items()}
        self.example_menu = tk.OptionMenu(
            self.main_container,
            self.example_var,
            *PADDED_EXAMPLES.keys(),
            command=lambda key: self.insert_example_prompt(key.strip())
        )
        self.example_menu.config(
            font=("Segoe UI", 10),
            bg="#21262d",
            fg="white",
            relief="flat",
            highlightthickness=0,
            width=24
        )
        dropdown_menu = self.example_menu["menu"]
        dropdown_menu.config(
            font=("Segoe UI", 10),
            bg="#21262d",
            fg="white",
            activebackground="#2ea043",
            activeforeground="white",
            tearoff=0
        )
        self.example_menu.pack(pady=(10, 0))

        self.contributors_page = ContributorsPage(self.main_container, self.show_prompt_view)
        self.contributors_button = ttk.Button(
            self.main_container,
            text="Contributors",
            command=self.show_contributors_page,
            style="Modern.TButton"
        )
        self.contributors_button.pack(pady=10)

        self.create_status_bar()

        self.animate_title()
        self.update_ai_status_indicator()
        self.apply_user_appearance()
         # ✅✅ Add this method to support "Switch User"
    def switch_user(self):
        messagebox.showinfo("Switch User", "User switching functionality will be implemented here.")


    def show_history_panel(self):
        if not self.history:
            messagebox.showinfo("History", "No history available.")
            return

        history_window = tk.Toplevel(self.root)
        history_window.title("Prompt History")
        history_window.geometry("600x400")
        history_window.configure(bg="#0d1117")

        listbox = tk.Listbox(
            history_window,
            bg="#161b22",
            fg="white",
            font=("Segoe UI", 10),
            selectbackground="#238636",
        selectforeground="white"
        )
        listbox.pack(fill="both", expand=True, padx=10, pady=10)

        for i, (prompt, code) in enumerate(self.history):
            entry = f"{i+1}. Prompt: {prompt[:60]}..." if len(prompt) > 60 else f"{i+1}. Prompt: {prompt}"
            listbox.insert(tk.END, entry)

        def show_selected():
            selected = listbox.curselection()
            if not selected:
                messagebox.showinfo("No selection", "Please select an entry to view.")
                return

            index = selected[0]
            prompt, code = self.history[index]

            detail_window = tk.Toplevel(history_window)
            detail_window.title(f"Prompt {index + 1} Details")
            detail_window.geometry("600x400")
            detail_window.configure(bg="#0d1117")

            text_widget = tk.Text(
                detail_window,
                wrap="word",
                bg="#161b22",
                fg="white",
                font=("Segoe UI", 10)
            )
            text_widget.insert(tk.END, f"Prompt:\n{prompt}\n\nOutput:\n{code}")
            text_widget.config(state=tk.DISABLED)
            text_widget.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Button(
            history_window,
            text="View Selected",
            command=show_selected,
            bg="#238636",
            fg="white",
            font=("Segoe UI", 10)
        ).pack(pady=5)


        def show_selected():
            idx = listbox.curselection()
            if idx:
                prompt, code = self.history[idx[0]]
                detail_window = tk.Toplevel(history_window)
                detail_window.title("History Detail")
                detail_window.geometry("600x400")
                detail_window.configure(bg="#0d1117")

                tk.Label(detail_window, text="Prompt:", bg="#0d1117", fg="white").pack(anchor="w", padx=10, pady=(10, 0))
                prompt_text = tk.Text(detail_window, wrap="word", bg="#21262d", fg="white")
                prompt_text.insert("1.0", prompt)
                prompt_text.config(state="disabled")
                prompt_text.pack(fill="both", expand=True, padx=10)

                tk.Label(detail_window, text="Generated Code:", bg="#0d1117", fg="white").pack(anchor="w", padx=10, pady=(10, 0))
                code_text = tk.Text(detail_window, wrap="word", bg="#21262d", fg="white")
                code_text.insert("1.0", code)
                code_text.config(state="disabled")
                code_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        tk.Button(history_window, text="View Selected", command=show_selected, bg="#238636", fg="white").pack(pady=5)


    def setup_window(self):
        self.root.title("Karbon - AI Web Builder")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)
        self.root.configure(bg='#0d1117')
        self.root.attributes('-alpha', 0.98)

        self.menu_bar = tk.Menu(self.root, bg="#21262d", fg="#c9d1d9", activebackground="#30363d",
                                activeforeground="#f0f6fc", relief="flat")
        self.root.config(menu=self.menu_bar)

        file_menu = tk.Menu(self.menu_bar, tearoff=0, bg="#21262d", fg="#c9d1d9")
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Code", command=self.handle_export)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)

        github_menu = tk.Menu(self.menu_bar, tearoff=0, bg="#21262d", fg="#c9d1d9")
        self.menu_bar.add_cascade(label="GitHub", menu=github_menu)
        github_menu.add_command(label="Manage Token", command=self.show_token_manager)

        view_menu = tk.Menu(self.menu_bar, tearoff=0, bg="#21262d", fg="#c9d1d9")
        self.menu_bar.add_cascade(label="View", menu=view_menu)
        self.prompt_view_visible = tk.BooleanVar(value=True)
        self.editor_view_visible = tk.BooleanVar(value=False)
        view_menu.add_checkbutton(label="Prompt View", onvalue=True, offvalue=False, variable=self.prompt_view_visible,
                                  command=self.toggle_prompt_view)
        view_menu.add_checkbutton(label="Editor View", onvalue=True, offvalue=False, variable=self.editor_view_visible,
                                  command=self.toggle_editor_view)

        layouts_menu = tk.Menu(self.menu_bar, tearoff=0, bg="#21262d", fg="#c9d1d9")
        self.menu_bar.add_cascade(label="Layouts", menu=layouts_menu)
        layouts_menu.add_command(label="Default", command=self.layout_default)
        layouts_menu.add_command(label="Coding Focus", command=self.layout_coding_focus)
        layouts_menu.add_command(label="Preview Focus", command=self.layout_preview_focus)

        contributors_menu = tk.Menu(self.menu_bar, tearoff=0, bg="#21262d", fg="#c9d1d9")
        self.menu_bar.add_cascade(label="Contributors", menu=contributors_menu)
        contributors_menu.add_command(label="View Contributors", command=self.show_contributors_page)

        self.center_window()

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure("TPanedWindow", background='#0d1117')
        style.configure("TPanedWindow.Sash", background='#30363d', sashthickness=6, relief='flat', borderwidth=0)
        style.map("TPanedWindow.Sash", background=[('active', '#58a6ff')])

        style.configure("Modern.TButton", background='#238636', foreground='white', borderwidth=0, focuscolor='none',
                        relief='flat', padding=(20, 10), font=("Segoe UI", 10))
        style.map("Modern.TButton", background=[('active', '#2ea043'), ('pressed', '#1a7f37')])
        style.configure("Modern.TEntry", fieldbackground='#21262d', borderwidth=1, relief='solid', insertcolor='white',
                        foreground='white')

    def create_title_bar(self):
        self.title_frame = tk.Frame(self.main_container, bg='#0d1117', height=80)
        self.title_frame.pack(fill="x", padx=20, pady=(20, 10))
        self.title_frame.pack_propagate(False)

        self.title_label = tk.Label(
            self.title_frame,
            text="⚡ KARBON",
            font=("Segoe UI", 28, "bold"),
            bg='#0d1117',
            fg='#58a6ff'
        )
        self.title_label.pack(side="left", pady=10)

        self.subtitle_label = tk.Label(
            self.title_frame,
            text="AI Web Builder",
            font=("Segoe UI", 12),
            bg='#0d1117',
            fg='#8b949e'
        )
        self.subtitle_label.pack(side="left", padx=(10, 0), pady=10)

        settings_btn = tk.Button(self.title_frame, text="⚙️", font=("Segoe UI", 16), bg='#21262d', fg='#8b949e',
                                 activebackground='#30363d', activeforeground='#f0f6fc', relief='flat', bd=0,
                                 cursor='hand2', command=self.open_settings)
        settings_btn.pack(side="right", padx=(10, 0))

        swap_btn = tk.Button(
            self.title_frame, text="🔄", font=("Segoe UI", 16), bg='#21262d', fg='#8b949e',
            activebackground='#30363d', activeforeground='#f0f6fc', relief='flat',
            bd=0, padx=0, pady=0, cursor='hand2', command=self.swap_panels
        )
        swap_btn.pack(side="right", padx=(10, 0))
        self.status_indicator = tk.Label(
            self.title_frame,
            text="●",
            font=("Segoe UI", 20),
            bg='#0d1117',
            fg='#3fb950'
        )

        

        self.status_indicator = tk.Label(
            self.title_frame,
            text="●",
            font=("Segoe UI", 20),
            bg='#0d1117',
            fg='#3fb950'
        )
        self.status_indicator.pack(side="right", pady=10)

        tk.Label(
            self.title_frame,
            text="v2.1",
            font=("Segoe UI", 10),
            bg='#0d1117',
            fg='#6e7681'
        ).pack(side="right", padx=(0, 10), pady=10)

        self.ai_status_label = tk.Label(
            self.title_frame,
            text="AI: Unknown",
            font=("Segoe UI", 10, "bold"),
            bg='#0d1117',
            fg='#d29922',
            anchor="e"
        )
        self.ai_status_label.pack(side="right", padx=(0, 20), pady=5)

    def create_status_bar(self):
        self.status_frame = tk.Frame(self.main_container, bg='#161b22', height=30)
        self.status_frame.pack(fill="x", side="bottom")
        self.status_frame.pack_propagate(False)
        self.status_label = tk.Label(self.status_frame, text="Ready to create amazing web experiences",
                                     font=("Segoe UI", 9), bg='#161b22', fg='#8b949e')
        self.status_label.pack(side="left", padx=20, pady=5)
        self.progress_var = tk.StringVar()
        self.progress_label = tk.Label(self.status_frame, textvariable=self.progress_var, font=("Segoe UI", 9),
                                       bg='#161b22', fg='#58a6ff')
        self.progress_label.pack(side="right", padx=20, pady=5)

    def update_ai_status_indicator(self):
        state = ai_status.get("state", "unknown")
        color_map = {"online": "#3fb950", "offline": "#f85149", "connecting": "#58a6ff", "error": '#d29922',
                     "unknown": "#6e7681"}
        color = color_map.get(state, "#6e7681")
        self.ai_status_label.config(text=f"AI: {state.capitalize()}", fg=color)
        self.root.after(2000, self.update_ai_status_indicator)

    def animate_title(self):
        colors = ['#58a6ff', '#79c0ff', '#a5d6ff', '#79c0ff', '#58a6ff']
        self.color_index = 0

        def cycle_colors():
            if hasattr(self, 'title_label') and self.title_label.winfo_exists():
                self.title_label.configure(fg=colors[self.color_index])
                self.color_index = (self.color_index + 1) % len(colors)
                self.root.after(2000, cycle_colors)

        cycle_colors()

    def update_status(self, message, progress=None):
        self.status_label.configure(text=message)
        self.progress_var.set(progress if progress else "")

    def get_code(self):
        return self.code

    def set_code(self, new_code):
        self.code = new_code
        self.update_status(f"Code updated - {len(new_code)} characters", "📝")
        
        # Update embedded preview if available
        try:
            if hasattr(self.editor_view, 'embedded_browser'):
                # Use simple embedded preview that opens in browser
                formatted_html = self.editor_view.format_html_for_preview(new_code)
                if self.editor_view.embedded_browser.update_content(formatted_html):
                    self.editor_view.preview_status.configure(text="● Updated", fg='#3fb950')
                    print("Preview opened in browser with full CSS support")
                else:
                    print("Failed to open preview in browser")
                        
            elif hasattr(self.editor_view, 'html_preview') and hasattr(self.editor_view.html_preview, 'set_html'):
                # Use tkhtmlview fallback
                simple_html = self.editor_view.create_simple_html_preview(new_code)
                self.editor_view.html_preview.set_html(simple_html)
                self.editor_view.preview_status.configure(text="● Updated", fg='#3fb950')
                
                # Also open in browser for guaranteed rendering
                formatted_html = self.editor_view.format_html_for_preview(new_code)
                temp_file = open_html_in_browser(formatted_html, "Karbon Preview")
                if temp_file:
                    print("Preview opened in browser for full rendering")
        except Exception as e:
            print(f"Error updating embedded preview: {e}")

    def handle_prompt_generated(self, prompt_text, code):
        self.code = code
        self.history.append((prompt_text, code))  # ✅ Save to history

        self.update_status("Code generated successfully!", "🎉")
        self.layout_preview_focus()

    # Update embedded preview if available
        try:
            if hasattr(self.editor_view, 'embedded_browser'):
                formatted_html = self.editor_view.format_html_for_preview(code)
                if self.editor_view.embedded_browser.update_content(formatted_html):
                    self.editor_view.preview_status.configure(text="● Updated", fg='#3fb950')
                    print("Preview opened in browser with full CSS support")
                else:
                    print("Failed to open preview in browser")

            elif hasattr(self.editor_view, 'html_preview') and hasattr(self.editor_view.html_preview, 'set_html'):
                simple_html = self.editor_view.create_simple_html_preview(code)
                self.editor_view.html_preview.set_html(simple_html)
                self.editor_view.preview_status.configure(text="● Updated", fg='#3fb950')

                formatted_html = self.editor_view.format_html_for_preview(code)
                temp_file = open_html_in_browser(formatted_html, "Karbon Preview")
                if temp_file:
                    print("Preview opened in browser for full rendering")
        except Exception as e:
            print(f"Error updating embedded preview: {e}")

    def get_api_key(self):
        return self.api_key

    def get_model_source(self):
        return self.model_source

    def insert_example_prompt(self, key):
        """Insert example prompt into the prompt input field"""
        if key and key in EXAMPLES:
            example_prompt = EXAMPLES[key]
            if hasattr(self, 'prompt_view') and hasattr(self.prompt_view, 'text_input'):
                # Clear existing content
                self.prompt_view.text_input.delete("1.0", "end")
                # Insert the example prompt
                self.prompt_view.text_input.insert("1.0", example_prompt)
                # Update text color to indicate it's not placeholder
                self.prompt_view.text_input.configure(fg='#f0f6fc')

    def toggle_prompt_view(self):
        is_present = self.prompt_view in self.paned_window.panes()
        if self.prompt_view_visible.get():
            if not is_present:
                self.paned_window.add(self.prompt_view, weight=1)
        else:
            if is_present:
                self.paned_window.forget(self.prompt_view)

    def toggle_editor_view(self):
        is_present = self.editor_view in self.paned_window.panes()
        if self.editor_view_visible.get():
            if not is_present:
                self.paned_window.add(self.editor_view, weight=1)
        else:
            if is_present:
                self.paned_window.forget(self.editor_view)

    def swap_panels(self):
        panes = self.paned_window.panes()
        if len(panes) == 2:
            first_pane = self.paned_window.pane(panes[0])
            second_pane = self.paned_window.pane(panes[1])

            self.paned_window.forget(panes[0])
            self.paned_window.forget(panes[1])

            self.paned_window.add(second_pane, weight=1)
            self.paned_window.add(first_pane, weight=1)

    def layout_default(self):
        for pane_widget_id in list(self.paned_window.panes()):
            self.paned_window.forget(pane_widget_id)
        self.paned_window.add(self.prompt_view, weight=1)
        self.prompt_view_visible.set(True)
        self.editor_view_visible.set(False)

    def layout_coding_focus(self):
        for pane_widget_id in list(self.paned_window.panes()):
            self.paned_window.forget(pane_widget_id)
        self.paned_window.add(self.editor_view, weight=1)
        self.prompt_view_visible.set(False)
        self.editor_view_visible.set(True)

    def layout_preview_focus(self):
        for pane_widget_id in list(self.paned_window.panes()):
            self.paned_window.forget(pane_widget_id)
        self.paned_window.add(self.prompt_view, weight=1)
        self.paned_window.add(self.editor_view, weight=1)
        self.prompt_view_visible.set(True)
        self.editor_view_visible.set(True)
        self.root.after(100, lambda: self.paned_window.sashpos(0, self.root.winfo_width() // 2))

    def save_settings(self):
        sash_position = None
        if len(self.paned_window.panes()) > 1:
            try:
                sash_position = self.paned_window.sashpos(0)
            except tk.TclError:
                sash_position = self.root.winfo_width() // 2

        layout_settings = {
            "prompt_view_visible": self.prompt_view_visible.get(),
            "editor_view_visible": self.editor_view_visible.get(),
            "sash_position": sash_position
        }
        settings = {
            "api_key": self.api_key,
            "model_source": self.model_source,
            "layout": layout_settings,
            "font_family": getattr(self, 'font_family', 'Segoe UI'),
            "font_size": int(getattr(self, 'font_size', 12)),
            "theme": getattr(self, 'theme', 'Dark')
        }
        try:
            with open("settings.json", "w") as f:
                json.dump(settings, f, indent=4)
            print("Settings saved.")
        except IOError as e:
            print(f"Error saving settings: {e}")

    def load_settings(self):
        self.font_family = 'Segoe UI'
        self.font_size = 12
        self.theme = 'Dark'

        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r") as f:
                    settings = json.load(f)
                    self.api_key = settings.get("api_key")
                    self.model_source = settings.get("model_source")
                    layout_settings = settings.get("layout")

                    if layout_settings:
                        self.prompt_view_visible.set(layout_settings.get("prompt_view_visible", True))
                        self.editor_view_visible.set(layout_settings.get("editor_view_visible", False))
                        sash_position = layout_settings.get("sash_position")

                        self.toggle_prompt_view()
                        self.toggle_editor_view()

                        def apply_sash():
                            if sash_position is not None and len(self.paned_window.panes()) > 1:
                                try:
                                    self.paned_window.sashpos(0, sash_position)
                                except tk.TclError:
                                    pass

                        self.root.after(100, apply_sash)

                    self.font_family = settings.get("font_family", self.font_family)
                    self.font_size = int(settings.get("font_size", self.font_size))
                    self.theme = settings.get("theme", self.theme)

            except (json.JSONDecodeError, KeyError, IOError) as e:
                print(f"Error reading settings.json ({e}), using default settings.")

        if not self.prompt_view_visible.get() and not self.editor_view_visible.get():
            self.layout_default()

    def open_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x450")
        settings_window.configure(bg='#161b22')
        settings_window.transient(self.root)
        settings_window.grab_set()

        tk.Label(settings_window, text="API Key:", bg='#161b22', fg='white', font=("Segoe UI", 10)).pack(pady=(20, 0))
        api_key_entry = ttk.Entry(settings_window, width=50, style="Modern.TEntry")
        api_key_entry.pack(pady=5, padx=20)
        if self.api_key:
            api_key_entry.insert(0, self.api_key)

        tk.Label(settings_window, text="Model Source URL (optional):", bg='#161b22', fg='white',
                 font=("Segoe UI", 10)).pack(pady=(10, 0))
        model_source_entry = ttk.Entry(settings_window, width=50, style="Modern.TEntry")
        model_source_entry.pack(pady=5, padx=20)
        if self.model_source:
            model_source_entry.insert(0, self.model_source)

        tk.Label(settings_window, text="Font Family:", bg='#161b22', fg='white', font=("Segoe UI", 10)).pack(
            pady=(15, 0))
        font_families = [
            "Segoe UI", "Arial", "Helvetica", "Times New Roman", "Courier New", "Verdana", "Tahoma", "Trebuchet MS",
            "Georgia", "Lucida Console"
        ]
        self.font_family_var = tk.StringVar(value=getattr(self, 'font_family', 'Segoe UI'))
        font_family_menu = ttk.Combobox(settings_window, textvariable=self.font_family_var, values=font_families,
                                        state="readonly")
        font_family_menu.pack(pady=5, padx=20)

        tk.Label(settings_window, text="Font Size:", bg='#161b22', fg='white', font=("Segoe UI", 10)).pack(pady=(10, 0))
        font_sizes = ["10", "11", "12", "14", "16", "18", "20", "22", "24"]
        self.font_size_var = tk.StringVar(value=str(getattr(self, 'font_size', 12)))
        font_size_menu = ttk.Combobox(settings_window, textvariable=self.font_size_var, values=font_sizes,
                                      state="readonly")
        font_size_menu.pack(pady=5, padx=20)

        tk.Label(settings_window, text="Theme:", bg='#161b22', fg='white', font=("Segoe UI", 10)).pack(pady=(10, 0))
        themes = [
            "Dark", "Light", "High Contrast", "Pastel", "Monokai", "Solarized Dark", "Solarized Light"
        ]
        self.theme_var = tk.StringVar(value=getattr(self, 'theme', 'Dark'))
        theme_menu = ttk.Combobox(settings_window, textvariable=self.theme_var, values=themes, state="readonly")
        theme_menu.pack(pady=5, padx=20)

        warning_label = tk.Label(settings_window, text="", bg='#161b22', fg='#f85149', font=("Segoe UI", 9),
                                 wraplength=350)
        warning_label.pack(pady=(5, 0))

        def save_and_close():
            self.api_key = api_key_entry.get()
            self.model_source = model_source_entry.get()
            self.font_family = self.font_family_var.get()
            self.font_size = int(self.font_size_var.get())
            new_theme = self.theme_var.get()

            theme_colors = self.get_theme_colors(new_theme)
            label_contrast = self.contrast_ratio(theme_colors["label_fg"], theme_colors["bg"])
            input_contrast = self.contrast_ratio(theme_colors["input_fg"], theme_colors["input_bg"])

            if label_contrast < 4.5 or input_contrast < 4.5:
                warning_label.config(
                    text="⚠️ Selected theme does not meet WCAG AA contrast standards. Consider another theme for better accessibility.")
                return
            else:
                warning_label.config(text="")

            self.theme = new_theme
            self.save_settings()
            self.apply_user_appearance()
            settings_window.destroy()

        save_btn = ttk.Button(settings_window, text="Save & Close", command=save_and_close, style="Modern.TButton")
        save_btn.pack(pady=20)

    def export_code_basic(self):
        try:
            from exporters.exporter import export_code
            if not self.code:
                self.show_notification("There is no code to export.", "warning")
                return
            export_code(self.code)
            self.show_notification("Code exported successfully!", "success")
        except ImportError:
            self.show_notification("Export functionality not available. 'exporter.py' module not found.", "error")
        except Exception as e:
            self.show_notification(f"Failed to export code: {e}", "error")

    def show_contributors_page(self):
        self.clear_content()
        self.contributors_page.pack(fill='both', expand=True)
        self.update_status("Viewing contributors", "👥")

    def show_prompt_view(self):
        self.clear_content()
        self.example_var.set("🔽 Choose Example Prompt")
        self.example_menu.pack(pady=(10, 0))
        self.contributors_button.pack(pady=10)

        self.paned_window.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.prompt_view_visible.set(True)
        self.editor_view_visible.set(False)
        self.toggle_prompt_view()
        self.toggle_editor_view()

        self.status_frame.pack(fill="x", side="bottom")

        self.update_status("Ready to create amazing web experiences", "🚀")

    def show_token_manager(self):
        self.clear_content()
        token_manager_view_instance = TokenManagerView(self.main_container, self.show_prompt_view)
        token_manager_view_instance.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        token_manager_view_instance.lift()

        self.status_frame.pack(fill="x", side="bottom")

        self.update_status("GitHub Token Manager", "🔐")

    def handle_export(self):
        from exporters.exporter import export_code, export_to_github, validate_github_token
        from core.token_manager import decrypt_token

        prompt = self.prompt_view.text_input.get("1.0", "end-1c").strip()
        if not prompt:
            self.show_notification("Please enter a description", "error")
            return

        print("⚙️ Generating code...")
        code = generate_code_from_prompt(prompt)

        path = export_code(code)
        if not path:
            self.show_notification("Export cancelled", "info")
            return

        token = decrypt_token()
        if not token:
            self.show_notification("No GitHub token found. Please set up your token in GitHub > Manage Token",
                                   "warning")
            return

        is_valid, username, error = validate_github_token()
        if not is_valid:
            self.show_notification(
                f"GitHub token is invalid: {error}. Please update your token in GitHub > Manage Token", "error")
            return

        print("📤 Attempting to push to GitHub...")
        url = export_to_github(code)
        if url:
            self.show_notification(f"Pushed to GitHub: {url}", "success")
        else:
            self.show_notification("Failed to push to GitHub. Check console for details.", "error")

    def show_notification(self, message, type="info"):
        colors = {
            "info": "#58a6ff",
            "success": "#3fb950",
                "error": "#f85149",
            "warning": "#d29922",
            "error": "#f85149"
        }

        notification = tk.Toplevel(self.root)
        notification.overrideredirect(True)
        notification.attributes('-topmost', True)
        notification.configure(bg='#21262d', relief="solid", borderwidth=1)

        self.root.update_idletasks()
        x = self.root.winfo_x() + self.root.winfo_width() - 320
        y = self.root.winfo_y() + 50
        notification.geometry(f"300x80+{x}+{y}")

        tk.Label(notification, text=message, font=("Segoe UI", 10), bg='#21262d', fg=colors.get(type, "#58a6ff"),
                 wraplength=280).pack(expand=True, padx=10, pady=10)
        notification.after(3000, notification.destroy)

    def get_theme_colors(self, theme_name):
        themes = {
            "Dark": {
                "bg": "#0d1117",
                "label_fg": "#f0f6fc",
                "input_bg": "#161b22",
                "input_fg": "#f0f6fc",
                "accent": "#58a6ff",
                "subtitle": "#8b949e",
                "warning": "#d29922",
                "success": "#3fb950",
                "error": "#f85149"
            },
            "Light": {
                "bg": "#f5f5f5",
                "label_fg": "#222222",
                "input_bg": "#ffffff",
                "input_fg": "#222222",
                "accent": "#0071f3",
                "subtitle": "#555555",
                "warning": "#e6a23c",
                "success": "#28a745",
                "error": "#dc3545"
            },
            "High Contrast": {
                "bg": "#000000",
                "label_fg": "#ffffff",
                "input_bg": "#000000",
                "input_fg": "#ffffff",
                "accent": "#ffea00",
                "subtitle": "#ffea00",
                "warning": "#ffd700",
                "success": "#39ff14",
                "error": "#ff0000"
            },
            "Pastel": {
                "bg": "#fdf6f0",
                "label_fg": "#5d576b",
                "input_bg": "#f7e7ce",
                "input_fg": "#5d576b",
                "accent": "#a3c9a8",
                "subtitle": "#b8a1a1",
                "warning": "#f0b400",
                "success": "#6ab04c",
                "error": "#e55353"
            },
            "Monokai": {
                "bg": "#272822",
                "label_fg": "#f8f8f2",
                "input_bg": "#272822",
                "input_fg": "#f8f8f2",
                "accent": "#f92672",
                "subtitle": "#a6e22e",
                "warning": "#fd971f",
                "success": "#a6e22e",
                "error": "#f92672"
            },
            "Solarized Dark": {
                "bg": "#002b36",
                "label_fg": "#93a1a1",
                "input_bg": "#073642",
                "input_fg": "#eee8d5",
                "accent": "#b58900",
                "subtitle": "#268bd2",
                "warning": "#cb4b16",
                "success": "#859900",
                "error": "#dc322f"
            },
            "Solarized Light": {
                "bg": "#fdf6e3",
                "label_fg": "#657b83",
                "input_bg": "#eee8d5",
                "input_fg": "#657b83",
                "accent": "#b58900",
                "subtitle": "#268bd2",
                "warning": "#dc322f",
                "success": "#859900",
                "error": "#dc322f"
            }
        }
        return themes.get(theme_name, themes["Dark"])

    def apply_user_appearance(self):
        font_family = getattr(self, 'font_family', 'Segoe UI')
        font_size = int(getattr(self, 'font_size', 12))
        theme = getattr(self, 'theme', 'Dark')
        theme_colors = self.get_theme_colors(theme)

        self.root.configure(bg=theme_colors["bg"])
        self.main_container.configure(bg=theme_colors["bg"])

        self.title_frame.configure(bg=theme_colors["bg"])
        self.title_label.configure(bg=theme_colors["bg"], fg=theme_colors["accent"], font=(font_family, 28, "bold"))
        self.subtitle_label.configure(bg=theme_colors["bg"], fg=theme_colors["subtitle"], font=(font_family, 12))
        self.ai_status_label.configure(bg=theme_colors["bg"], font=(font_family, 10, "bold"))

        self.status_frame.configure(bg=theme_colors["input_bg"])
        self.status_label.configure(bg=theme_colors["input_bg"], fg=theme_colors["subtitle"], font=(font_family, 9))
        self.progress_label.configure(bg=theme_colors["input_bg"], fg=theme_colors["accent"], font=(font_family, 9))

        self.example_menu.config(
            font=(font_family, 10),
            bg=theme_colors["input_bg"],
            fg=theme_colors["input_fg"]
        )
        dropdown_menu = self.example_menu["menu"]
        dropdown_menu.config(
            font=(font_family, 10),
            bg=theme_colors["input_bg"],
            fg=theme_colors["input_fg"],
            activebackground=theme_colors["accent"],
            activeforeground=theme_colors["label_fg"]
        )

        style = ttk.Style()
        style.configure("Modern.TButton", font=(font_family, 10), background=theme_colors["accent"], foreground='white')
        style.map("Modern.TButton", background=[('active', theme_colors["accent"])])

        if hasattr(self, 'prompt_view'):
            self.prompt_view.update_appearance(font_family, font_size, theme_colors)
        if hasattr(self, 'editor_view'):
            self.editor_view.update_appearance(font_family, font_size, theme_colors)
        if hasattr(self, 'contributors_page'):
            self.contributors_page.update_appearance(font_family, font_size, theme_colors)

        self.menu_bar.config(bg=theme_colors["input_bg"], fg=theme_colors["label_fg"],
                             activebackground=theme_colors["accent"], activeforeground=theme_colors["label_fg"])
        for menu in [self.menu_bar.winfo_children()]:
            if isinstance(menu, tk.Menu):
                menu.config(bg=theme_colors["input_bg"], fg=theme_colors["label_fg"],
                            activebackground=theme_colors["accent"], activeforeground=theme_colors["label_fg"])

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        lv = len(hex_color)
        return tuple(int(hex_color[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

    def luminance(self, rgb):
        r, g, b = [x / 255.0 for x in rgb]
        a = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in (r, g, b)]
        return 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2]

    def contrast_ratio(self, color1_hex, color2_hex):
        lum1 = self.luminance(self.hex_to_rgb(color1_hex))
        lum2 = self.luminance(self.hex_to_rgb(color2_hex))
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        return (lighter + 0.05) / (darker + 0.05)

    def clear_content(self):
        for pane_widget_id in list(self.paned_window.panes()):
            self.paned_window.forget(pane_widget_id)

        self.contributors_page.pack_forget()
        self.example_menu.pack_forget()
        self.contributors_button.pack_forget()
        self.paned_window.pack_forget()
        self.status_frame.pack_forget()

    def show_contributors_page(self):
        self.clear_content()
        self.contributors_page.pack(fill='both', expand=True)
        self.update_status("Viewing contributors", "👥")

    def show_prompt_view(self):
        self.clear_content()
        self.example_var.set("🔽 Choose Example Prompt")
        self.example_menu.pack(pady=(10, 0))
        self.contributors_button.pack(pady=10)

        self.paned_window.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.prompt_view_visible.set(True)
        self.editor_view_visible.set(False)
        self.toggle_prompt_view()
        self.toggle_editor_view()

        self.status_frame.pack(fill="x", side="bottom")

        self.update_status("Ready to create amazing web experiences", "🚀")

    def show_token_manager(self):
        self.clear_content()
        token_manager_view_instance = TokenManagerView(self.main_container, self.show_prompt_view)
        token_manager_view_instance.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        token_manager_view_instance.lift()

        self.status_frame.pack(fill="x", side="bottom")

        self.update_status("GitHub Token Manager", "🔐")

    def handle_export(self):
        from exporters.exporter import export_code, export_to_github, validate_github_token
        from core.token_manager import decrypt_token

        prompt = self.prompt_view.text_input.get("1.0", "end-1c").strip()
        if not prompt:
            self.show_notification("Please enter a description", "error")
            return

        print("⚙️ Generating code...")
        code = generate_code_from_prompt(prompt)

        path = export_code(code)
        if not path:
            self.show_notification("Export cancelled", "info")
            return

        token = decrypt_token()
        if not token:
            self.show_notification("No GitHub token found. Please set up your token in GitHub > Manage Token",
                                   "warning")
            return

        is_valid, username, error = validate_github_token()
        if not is_valid:
            self.show_notification(
                f"GitHub token is invalid: {error}. Please update your token in GitHub > Manage Token", "error")
            return

        print("📤 Attempting to push to GitHub...")
        url = export_to_github(code)
        if url:
            self.show_notification(f"Pushed to GitHub: {url}", "success")
        else:
            self.show_notification("Failed to push to GitHub. Check console for details.", "error")

    def show_notification(self, message, type="info"):
        colors = {
            "info": "#58a6ff",
            "success": "#3fb950",
                "error": "#f85149",
            "warning": "#d29922",
            "error": "#f85149"
        }

        notification = tk.Toplevel(self.root)
        notification.overrideredirect(True)
        notification.attributes('-topmost', True)
        notification.configure(bg='#21262d', relief="solid", borderwidth=1)

        self.root.update_idletasks()
        x = self.root.winfo_x() + self.root.winfo_width() - 320
        y = self.root.winfo_y() + 50
        notification.geometry(f"300x80+{x}+{y}")

        tk.Label(notification, text=message, font=("Segoe UI", 10), bg='#21262d', fg=colors.get(type, "#58a6ff"),
                 wraplength=280).pack(expand=True, padx=10, pady=10)
        notification.after(3000, notification.destroy)

    def get_theme_colors(self, theme_name):
        themes = {
            "Dark": {
                "bg": "#0d1117",
                "label_fg": "#f0f6fc",
                "input_bg": "#161b22",
                "input_fg": "#f0f6fc",
                "accent": "#58a6ff",
                "subtitle": "#8b949e",
                "warning": "#d29922",
                "success": "#3fb950",
                "error": "#f85149"
            },
            "Light": {
                "bg": "#f5f5f5",
                "label_fg": "#222222",
                "input_bg": "#ffffff",
                "input_fg": "#222222",
                "accent": "#0071f3",
                "subtitle": "#555555",
                "warning": "#e6a23c",
                "success": "#28a745",
                "error": "#dc3545"
            },
            "High Contrast": {
                "bg": "#000000",
                "label_fg": "#ffffff",
                "input_bg": "#000000",
                "input_fg": "#ffffff",
                "accent": "#ffea00",
                "subtitle": "#ffea00",
                "warning": "#ffd700",
                "success": "#39ff14",
                "error": "#ff0000"
            },
            "Pastel": {
                "bg": "#fdf6f0",
                "label_fg": "#5d576b",
                "input_bg": "#f7e7ce",
                "input_fg": "#5d576b",
                "accent": "#a3c9a8",
                "subtitle": "#b8a1a1",
                "warning": "#f0b400",
                "success": "#6ab04c",
                "error": "#e55353"
            },
            "Monokai": {
                "bg": "#272822",
                "label_fg": "#f8f8f2",
                "input_bg": "#272822",
                "input_fg": "#f8f8f2",
                "accent": "#f92672",
                "subtitle": "#a6e22e",
                "warning": "#fd971f",
                "success": "#a6e22e",
                "error": "#f92672"
            },
            "Solarized Dark": {
                "bg": "#002b36",
                "label_fg": "#93a1a1",
                "input_bg": "#073642",
                "input_fg": "#eee8d5",
                "accent": "#b58900",
                "subtitle": "#268bd2",
                "warning": "#cb4b16",
                "success": "#859900",
                "error": "#dc322f"
            },
            "Solarized Light": {
                "bg": "#fdf6e3",
                "label_fg": "#657b83",
                "input_bg": "#eee8d5",
                "input_fg": "#657b83",
                "accent": "#b58900",
                "subtitle": "#268bd2",
                "warning": "#dc322f",
                "success": "#859900",
                "error": "#dc322f"
            }
        }
        return themes.get(theme_name, themes["Dark"])

    def apply_user_appearance(self):
        font_family = getattr(self, 'font_family', 'Segoe UI')
        font_size = int(getattr(self, 'font_size', 12))
        theme = getattr(self, 'theme', 'Dark')
        theme_colors = self.get_theme_colors(theme)

        self.root.configure(bg=theme_colors["bg"])
        self.main_container.configure(bg=theme_colors["bg"])

        self.title_frame.configure(bg=theme_colors["bg"])
        self.title_label.configure(bg=theme_colors["bg"], fg=theme_colors["accent"], font=(font_family, 28, "bold"))
        self.subtitle_label.configure(bg=theme_colors["bg"], fg=theme_colors["subtitle"], font=(font_family, 12))
        self.ai_status_label.configure(bg=theme_colors["bg"], font=(font_family, 10, "bold"))

        self.status_frame.configure(bg=theme_colors["input_bg"])
        self.status_label.configure(bg=theme_colors["input_bg"], fg=theme_colors["subtitle"], font=(font_family, 9))
        self.progress_label.configure(bg=theme_colors["input_bg"], fg=theme_colors["accent"], font=(font_family, 9))

        self.example_menu.config(
            font=(font_family, 10),
            bg=theme_colors["input_bg"],
            fg=theme_colors["input_fg"]
        )
        dropdown_menu = self.example_menu["menu"]
        dropdown_menu.config(
            font=(font_family, 10),
            bg=theme_colors["input_bg"],
            fg=theme_colors["input_fg"],
            activebackground=theme_colors["accent"],
            activeforeground=theme_colors["label_fg"]
        )

        style = ttk.Style()
        style.configure("Modern.TButton", font=(font_family, 10), background=theme_colors["accent"], foreground='white')
        style.map("Modern.TButton", background=[('active', theme_colors["accent"])])

        if hasattr(self, 'prompt_view'):
            self.prompt_view.update_appearance(font_family, font_size, theme_colors)
        if hasattr(self, 'editor_view'):
            self.editor_view.update_appearance(font_family, font_size, theme_colors)
        if hasattr(self, 'contributors_page'):
            self.contributors_page.update_appearance(font_family, font_size, theme_colors)

        self.menu_bar.config(bg=theme_colors["input_bg"], fg=theme_colors["label_fg"],
                             activebackground=theme_colors["accent"], activeforeground=theme_colors["label_fg"])
        for menu in [self.menu_bar.winfo_children()]:
            if isinstance(menu, tk.Menu):
                menu.config(bg=theme_colors["input_bg"], fg=theme_colors["label_fg"],
                            activebackground=theme_colors["accent"], activeforeground=theme_colors["label_fg"])

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        lv = len(hex_color)
        return tuple(int(hex_color[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

    def luminance(self, rgb):
        r, g, b = [x / 255.0 for x in rgb]
        a = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in (r, g, b)]
        return 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2]

    def contrast_ratio(self, color1_hex, color2_hex):
        lum1 = self.luminance(self.hex_to_rgb(color1_hex))
        lum2 = self.luminance(self.hex_to_rgb(color2_hex))
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        return (lighter + 0.05) / (darker + 0.05)

    def clear_content(self):
        for pane_widget_id in list(self.paned_window.panes()):
            self.paned_window.forget(pane_widget_id)

        self.contributors_page.pack_forget()
        self.example_menu.pack_forget()
        self.contributors_button.pack_forget()
        self.paned_window.pack_forget()
        self.status_frame.pack_forget()

    def show_contributors_page(self):
        self.clear_content()
        self.contributors_page.pack(fill='both', expand=True)
        self.update_status("Viewing contributors", "👥")

    def show_prompt_view(self):
        self.clear_content()
        self.example_var.set("🔽 Choose Example Prompt")
        self.example_menu.pack(pady=(10, 0))
        self.contributors_button.pack(pady=10)

        self.paned_window.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.prompt_view_visible.set(True)
        self.editor_view_visible.set(False)
        self.toggle_prompt_view()
        self.toggle_editor_view()

        self.status_frame.pack(fill="x", side="bottom")

        self.update_status("Ready to create amazing web experiences", "🚀")

    def show_token_manager(self):
        self.clear_content()
        token_manager_view_instance = TokenManagerView(self.main_container, self.show_prompt_view)
        token_manager_view_instance.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        token_manager_view_instance.lift()

        self.status_frame.pack(fill="x", side="bottom")

        self.update_status("GitHub Token Manager", "🔐")

    def handle_export(self):
        from exporters.exporter import export_code, export_to_github, validate_github_token
        from core.token_manager import decrypt_token

        prompt = self.prompt_view.text_input.get("1.0", "end-1c").strip()
        if not prompt:
            self.show_notification("Please enter a description", "error")
            return

        print("⚙️ Generating code...")
        code = generate_code_from_prompt(prompt)

        path = export_code(code)
        if not path:
            self.show_notification("Export cancelled", "info")
            return

        token = decrypt_token()
        if not token:
            self.show_notification("No GitHub token found. Please set up your token in GitHub > Manage Token",
                                   "warning")
            return

        is_valid, username, error = validate_github_token()
        if not is_valid:
            self.show_notification(
                f"GitHub token is invalid: {error}. Please update your token in GitHub > Manage Token", "error")
            return

        print("📤 Attempting to push to GitHub...")
        url = export_to_github(code)
        if url:
            self.show_notification(f"Pushed to GitHub: {url}", "success")
        else:
            self.show_notification("Failed to push to GitHub. Check console for details.", "error")

    def show_notification(self, message, type="info"):
        colors = {
            "info": "#58a6ff",
            "success": "#3fb950",
                "error": "#f85149",
            "warning": "#d29922",
            "error": "#f85149"
        }

        notification = tk.Toplevel(self.root)
        notification.overrideredirect(True)
        notification.attributes('-topmost', True)
        notification.configure(bg='#21262d', relief="solid", borderwidth=1)

        self.root.update_idletasks()
        x = self.root.winfo_x() + self.root.winfo_width() - 320
        y = self.root.winfo_y() + 50
        notification.geometry(f"300x80+{x}+{y}")

        tk.Label(notification, text=message, font=("Segoe UI", 10), bg='#21262d', fg=colors.get(type, "#58a6ff"),
                 wraplength=280).pack(expand=True, padx=10, pady=10)
        notification.after(3000, notification.destroy)

    def get_theme_colors(self, theme_name):
        themes = {
            "Dark": {
                "bg": "#0d1117",
                "label_fg": "#f0f6fc",
                "input_bg": "#161b22",
                "input_fg": "#f0f6fc",
                "accent": "#58a6ff",
                "subtitle": "#8b949e",
                "warning": "#d29922",
                "success": "#3fb950",
                "error": "#f85149"
            },
            "Light": {
                "bg": "#f5f5f5",
                "label_fg": "#222222",
                "input_bg": "#ffffff",
                "input_fg": "#222222",
                "accent": "#0071f3",
                "subtitle": "#555555",
                "warning": "#e6a23c",
                "success": "#28a745",
                "error": "#dc3545"
            },
            "High Contrast": {
                "bg": "#000000",
                "label_fg": "#ffffff",
                "input_bg": "#000000",
                "input_fg": "#ffffff",
                "accent": "#ffea00",
                "subtitle": "#ffea00",
                "warning": "#ffd700",
                "success": "#39ff14",
                "error": "#ff0000"
            },
            "Pastel": {
                "bg": "#fdf6f0",
                "label_fg": "#5d576b",
                "input_bg": "#f7e7ce",
                "input_fg": "#5d576b",
                "accent": "#a3c9a8",
                "subtitle": "#b8a1a1",
                "warning": "#f0b400",
                "success": "#6ab04c",
                "error": "#e55353"
            },
            "Monokai": {
                "bg": "#272822",
                "label_fg": "#f8f8f2",
                "input_bg": "#272822",
                "input_fg": "#f8f8f2",
                "accent": "#f92672",
                "subtitle": "#a6e22e",
                "warning": "#fd971f",
                "success": "#a6e22e",
                "error": "#f92672"
            },
            "Solarized Dark": {
                "bg": "#002b36",
                "label_fg": "#93a1a1",
                "input_bg": "#073642",
                "input_fg": "#eee8d5",
                "accent": "#b58900",
                "subtitle": "#268bd2",
                "warning": "#cb4b16",
                "success": "#859900",
                "error": "#dc322f"
            },
            "Solarized Light": {
                "bg": "#fdf6e3",
                "label_fg": "#657b83",
                "input_bg": "#eee8d5",
                "input_fg": "#657b83",
                "accent": "#b58900",
                "subtitle": "#268bd2",
                "warning": "#dc322f",
                "success": "#859900",
                "error": "#dc322f"
            }
        }
        return themes.get(theme_name, themes["Dark"])

    def apply_user_appearance(self):
        font_family = getattr(self, 'font_family', 'Segoe UI')
        font_size = int(getattr(self, 'font_size', 12))
        theme = getattr(self, 'theme', 'Dark')
        theme_colors = self.get_theme_colors(theme)

        self.root.configure(bg=theme_colors["bg"])
        self.main_container.configure(bg=theme_colors["bg"])

        self.title_frame.configure(bg=theme_colors["bg"])
        self.title_label.configure(bg=theme_colors["bg"], fg=theme_colors["accent"], font=(font_family, 28, "bold"))
        self.subtitle_label.configure(bg=theme_colors["bg"], fg=theme_colors["subtitle"], font=(font_family, 12))
        self.ai_status_label.configure(bg=theme_colors["bg"], font=(font_family, 10, "bold"))

        self.status_frame.configure(bg=theme_colors["input_bg"])
        self.status_label.configure(bg=theme_colors["input_bg"], fg=theme_colors["subtitle"], font=(font_family, 9))
        self.progress_label.configure(bg=theme_colors["input_bg"], fg=theme_colors["accent"], font=(font_family, 9))

        self.example_menu.config(
            font=(font_family, 10),
            bg=theme_colors["input_bg"],
            fg=theme_colors["input_fg"]
        )
        dropdown_menu = self.example_menu["menu"]
        dropdown_menu.config(
            font=(font_family, 10),
            bg=theme_colors["input_bg"],
            fg=theme_colors["input_fg"],
            activebackground=theme_colors["accent"],
            activeforeground=theme_colors["label_fg"]
        )

        style = ttk.Style()
        style.configure("Modern.TButton", font=(font_family, 10), background=theme_colors["accent"], foreground='white')
        style.map("Modern.TButton", background=[('active', theme_colors["accent"])])

        if hasattr(self, 'prompt_view'):
            self.prompt_view.update_appearance(font_family, font_size, theme_colors)
        if hasattr(self, 'editor_view'):
            self.editor_view.update_appearance(font_family, font_size, theme_colors)
        if hasattr(self, 'contributors_page'):
            self.contributors_page.update_appearance(font_family, font_size, theme_colors)

        self.menu_bar.config(bg=theme_colors["input_bg"], fg=theme_colors["label_fg"],
                             activebackground=theme_colors["accent"], activeforeground=theme_colors["label_fg"])
        for menu in [self.menu_bar.winfo_children()]:
            if isinstance(menu, tk.Menu):
                menu.config(bg=theme_colors["input_bg"], fg=theme_colors["label_fg"],
                            activebackground=theme_colors["accent"], activeforeground=theme_colors["label_fg"])

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        lv = len(hex_color)
        return tuple(int(hex_color[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

    def luminance(self, rgb):
        r, g, b = [x / 255.0 for x in rgb]
        a = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in (r, g, b)]
        return 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2]

    def contrast_ratio(self, color1_hex, color2_hex):
        lum1 = self.luminance(self.hex_to_rgb(color1_hex))
        lum2 = self.luminance(self.hex_to_rgb(color2_hex))
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        return (lighter + 0.05) / (darker + 0.05)

    def clear_content(self):
        for pane_widget_id in list(self.paned_window.panes()):
            self.paned_window.forget(pane_widget_id)

        self.contributors_page.pack_forget()
        self.example_menu.pack_forget()
        self.contributors_button.pack_forget()
        self.paned_window.pack_forget()
        self.status_frame.pack_forget()

    def show_contributors_page(self):
        self.clear_content()
        self.contributors_page.pack(fill='both', expand=True)
        self.update_status("Viewing contributors", "👥")

    def show_prompt_view(self):
        self.clear_content()
        self.example_var.set("🔽 Choose Example Prompt")
        self.example_menu.pack(pady=(10, 0))
        self.contributors_button.pack(pady=10)

        self.paned_window.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.prompt_view_visible.set(True)
        self.editor_view_visible.set(False)
        self.toggle_prompt_view()
        self.toggle_editor_view()

        self.status_frame.pack(fill="x", side="bottom")

        self.update_status("Ready to create amazing web experiences", "🚀")

    def show_token_manager(self):
        self.clear_content()
        token_manager_view_instance = TokenManagerView(self.main_container, self.show_prompt_view)
        token_manager_view_instance.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        token_manager_view_instance.lift()

        self.status_frame.pack(fill="x", side="bottom")

        self.update_status("GitHub Token Manager", "🔐")

    def handle_export(self):
        from exporters.exporter import export_code, export_to_github, validate_github_token
        from core.token_manager import decrypt_token

        prompt = self.prompt_view.text_input.get("1.0", "end-1c").strip()
        if not prompt:
            self.show_notification("Please enter a description", "error")
            return

        print("⚙️ Generating code...")
        code = generate_code_from_prompt(prompt)

        path = export_code(code)
        if not path:
            self.show_notification("Export cancelled", "info")
            return

        token = decrypt_token()
        if not token:
            self.show_notification("No GitHub token found. Please set up your token in GitHub > Manage Token",
                                   "warning")
            return

        is_valid, username, error = validate_github_token()
        if not is_valid:
            self.show_notification(
                f"GitHub token is invalid: {error}. Please update your token in GitHub > Manage Token", "error")
            return

        print("📤 Attempting to push to GitHub...")
        url = export_to_github(code)
        if url:
            self.show_notification(f"Pushed to GitHub: {url}", "success")
        else:
            self.show_notification("Failed to push to GitHub. Check console for details.", "error")

    def show_notification(self, message, type="info"):
        colors = {
            "info": "#58a6ff",
            "success": "#3fb950",
                "error": "#f85149",
            "warning": "#d29922",
            "error": "#f85149"
        }

        notification = tk.Toplevel(self.root)
        notification.overrideredirect(True)
        notification.attributes('-topmost', True)
        notification.configure(bg='#21262d', relief="solid", borderwidth=1)

        self.root.update_idletasks()
        x = self.root.winfo_x() + self.root.winfo_width() - 320
        y = self.root.winfo_y() + 50
        notification.geometry(f"300x80+{x}+{y}")

        tk.Label(notification, text=message, font=("Segoe UI", 10), bg='#21262d', fg=colors.get(type, "#58a6ff"),
                 wraplength=280).pack(expand=True, padx=10, pady=10)
        notification.after(3000, notification.destroy)

    def get_theme_colors(self, theme_name):
        themes = {
            "Dark": {
                "bg": "#0d1117",
                "label_fg": "#f0f6fc",
                "input_bg": "#161b22",
                "input_fg": "#f0f6fc",
                "accent": "#58a6ff",
                "subtitle": "#8b949e",
                "warning": "#d29922",
                "success": "#3fb950",
                "error": "#f85149"
            },
            "Light": {
                "bg": "#f5f5f5",
                "label_fg": "#222222",
                "input_bg": "#ffffff",
                "input_fg": "#222222",
                "accent": "#0071f3",
                "subtitle": "#555555",
                "warning": "#e6a23c",
                "success": "#28a745",
                "error": "#dc3545"
            },
            "High Contrast": {
                "bg": "#000000",
                "label_fg": "#ffffff",
                "input_bg": "#000000",
                "input_fg": "#ffffff",
                "accent": "#ffea00",
                "subtitle": "#ffea00",
                "warning": "#ffd700",
                "success": "#39ff14",
                "error": "#ff0000"
            },
            "Pastel": {
                "bg": "#fdf6f0",
                "label_fg": "#5d576b",
                "input_bg": "#f7e7ce",
                "input_fg": "#5d576b",
                "accent": "#a3c9a8",
                "subtitle": "#b8a1a1",
                "warning": "#f0b400",
                "success": "#6ab04c",
                "error": "#e55353"
            },
            "Monokai": {
                "bg": "#272822",
                "label_fg": "#f8f8f2",
                "input_bg": "#272822",
                "input_fg": "#f8f8f2",
                "accent": "#f92672",
                "subtitle": "#a6e22e",
                "warning": "#fd971f",
                "success": "#a6e22e",
                "error": "#f92672"
            },
            "Solarized Dark": {
                "bg": "#002b36",
                "label_fg": "#93a1a1",
                "input_bg": "#073642",
                "input_fg": "#eee8d5",
                "accent": "#b58900",
                "subtitle": "#268bd2",
                "warning": "#cb4b16",
                "success": "#859900",
                "error": "#dc322f"
            },
            "Solarized Light": {
                "bg": "#fdf6e3",
                "label_fg": "#657b83",
                "input_bg": "#eee8d5",
                "input_fg": "#657b83",
                "accent": "#b58900",
                "subtitle": "#268bd2",
                "warning": "#dc322f",
                "success": "#859900",
                "error": "#dc322f"
            }
        }
        return themes.get(theme_name, themes["Dark"])

    def apply_user_appearance(self):
        font_family = getattr(self, 'font_family', 'Segoe UI')
        font_size = int(getattr(self, 'font_size', 12))
        theme = getattr(self, 'theme', 'Dark')
        theme_colors = self.get_theme_colors(theme)

        self.root.configure(bg=theme_colors["bg"])
        self.main_container.configure(bg=theme_colors["bg"])

        self.title_frame.configure(bg=theme_colors["bg"])
        self.title_label.configure(bg=theme_colors["bg"], fg=theme_colors["accent"], font=(font_family, 28, "bold"))
        self.subtitle_label.configure(bg=theme_colors["bg"], fg=theme_colors["subtitle"], font=(font_family, 12))
        self.ai_status_label.configure(bg=theme_colors["bg"], font=(font_family, 10, "bold"))

        self.status_frame.configure(bg=theme_colors["input_bg"])
        self.status_label.configure(bg=theme_colors["input_bg"], fg=theme_colors["subtitle"], font=(font_family, 9))
        self.progress_label.configure(bg=theme_colors["input_bg"], fg=theme_colors["accent"], font=(font_family, 9))

        self.example_menu.config(
            font=(font_family, 10),
            bg=theme_colors["input_bg"],
            fg=theme_colors["input_fg"]
        )
        dropdown_menu = self.example_menu["menu"]
        dropdown_menu.config(
            font=(font_family, 10),
            bg=theme_colors["input_bg"],
            fg=theme_colors["input_fg"],
            activebackground=theme_colors["accent"],
            activeforeground=theme_colors["label_fg"]
        )

        style = ttk.Style()
        style.configure("Modern.TButton", font=(font_family, 10), background=theme_colors["accent"], foreground='white')
        style.map("Modern.TButton", background=[('active', theme_colors["accent"])])

        if hasattr(self, 'prompt_view'):
            self.prompt_view.update_appearance(font_family, font_size, theme_colors)
        if hasattr(self, 'editor_view'):
            self.editor_view.update_appearance(font_family, font_size, theme_colors)
        if hasattr(self, 'contributors_page'):
            self.contributors_page.update_appearance(font_family, font_size, theme_colors)

        self.menu_bar.config(bg=theme_colors["input_bg"], fg=theme_colors["label_fg"],
                             activebackground=theme_colors["accent"], activeforeground=theme_colors["label_fg"])
        for menu in [self.menu_bar.winfo_children()]:
            if isinstance(menu, tk.Menu):
                menu.config(bg=theme_colors["input_bg"], fg=theme_colors["label_fg"],
                            activebackground=theme_colors["accent"], activeforeground=theme_colors["label_fg"])

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        lv = len(hex_color)
        return tuple(int(hex_color[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

    def luminance(self, rgb):
        r, g, b = [x / 255.0 for x in rgb]
        a = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in (r, g, b)]
        return 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2]

    def contrast_ratio(self, color1_hex, color2_hex):
        lum1 = self.luminance(self.hex_to_rgb(color1_hex))
        lum2 = self.luminance(self.hex_to_rgb(color2_hex))
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        return (lighter + 0.05) / (darker + 0.05)

    def clear_content(self):
        for pane_widget_id in list(self.paned_window.panes()):
            self.paned_window.forget(pane_widget_id)

        self.contributors_page.pack_forget()
        self.example_menu.pack_forget()
        self.contributors_button.pack_forget()
        self.paned_window.pack_forget()
        self.status_frame.pack_forget()

    def show_contributors_page(self):
        self.clear_content()
        self.contributors_page.pack(fill='both', expand=True)
        self.update_status("Viewing contributors", "👥")

    def show_prompt_view(self):
        self.clear_content()
        self.example_var.set("🔽 Choose Example Prompt")
        self.example_menu.pack(pady=(10, 0))
        self.contributors_button.pack(pady=10)

        self.paned_window.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.prompt_view_visible.set(True)
        self.editor_view_visible.set(False)
        self.toggle_prompt_view()
        self.toggle_editor_view()

        self.status_frame.pack(fill="x", side="bottom")

        self.update_status("Ready to create amazing web experiences", "🚀")

    def show_token_manager(self):
        self.clear_content()
        token_manager_view_instance = TokenManagerView(self.main_container, self.show_prompt_view)
        token_manager_view_instance.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        token_manager_view_instance.lift()

        self.status_frame.pack(fill="x", side="bottom")

        self.update_status("GitHub Token Manager", "🔐")

    def handle_export(self):
        from exporters.exporter import export_code, export_to_github, validate_github_token
        from core.token_manager import decrypt_token

        prompt = self.prompt_view.text_input.get("1.0", "end-1c").strip()
        if not prompt:
            self.show_notification("Please enter a description", "error")
            return

        print("⚙️ Generating code...")
        code = generate_code_from_prompt(prompt)

        path = export_code(code)
        if not path:
            self.show_notification("Export cancelled", "info")
            return

        token = decrypt_token()
        if not token:
            self.show_notification("No GitHub token found. Please set up your token in GitHub > Manage Token",
                                   "warning")
            return

        is_valid, username, error = validate_github_token()
        if not is_valid:
            self.show_notification(
                f"GitHub token is invalid: {error}. Please update your token in GitHub > Manage Token", "error")
            return

        print("📤 Attempting to push to GitHub...")
        url = export_to_github(code)
        if url:
            self.show_notification(f"Pushed to GitHub: {url}", "success")
        else:
            self.show_notification("Failed to push to GitHub. Check console for details.", "error")

    def show_notification(self, message, type="info"):
        colors = {
            "info": "#58a6ff",
            "success": "#3fb950",
                "error": "#f85149",
            "warning": "#d29922",
            "error": "#f85149"
        }

        notification = tk.Toplevel(self.root)
        notification.overrideredirect(True)
        notification.attributes('-topmost', True)
        notification.configure(bg='#21262d', relief="solid", borderwidth=1)

        self.root.update_idletasks()
        x = self.root.winfo_x() + self.root.winfo_width() - 320
        y = self.root.winfo_y() + 50
        notification.geometry(f"300x80+{x}+{y}")

        tk.Label(notification, text=message, font=("Segoe UI", 10), bg='#21262d', fg=colors.get(type, "#58a6ff"),
                 wraplength=280).pack(expand=True, padx=10, pady=10)
        notification.after(3000, notification.destroy)

    def get_theme_colors(self, theme_name):
        themes = {
            "Dark": {
                "bg": "#0d1117",
                "label_fg": "#f0f6fc",
                "input_bg": "#161b22",
                "input_fg": "#f0f6fc",
                "accent": "#58a6ff",
                "subtitle": "#8b949e",
                "warning": "#d29922",
                "success": "#3fb950",
                "error": "#f85149"
            },
            "Light": {
                "bg": "#f5f5f5",
                "label_fg": "#222222",
                "input_bg": "#ffffff",
                "input_fg": "#222222",
                "accent": "#0071f3",
                "subtitle": "#555555",
                "warning": "#e6a23c",
                "success": "#28a745",
                "error": "#dc3545"
            },
            "High Contrast": {
                "bg": "#000000",
                "label_fg": "#ffffff",
                "input_bg": "#000000",
                "input_fg": "#ffffff",
                "accent": "#ffea00",
                "subtitle": "#ffea00",
                "warning": "#ffd700",
                "success": "#39ff14",
                "error": "#ff0000"
            },
            "Pastel": {
                "bg": "#fdf6f0",
                "label_fg": "#5d576b",
                "input_bg": "#f7e7ce",
                "input_fg": "#5d576b",
                "accent": "#a3c9a8",
                "subtitle": "#b8a1a1",
                "warning": "#f0b400",
                "success": "#6ab04c",
                "error": "#e55353"
            },
            "Monokai": {
                "bg": "#272822",
                "label_fg": "#f8f8f2",
                "input_bg": "#272822",
                "input_fg": "#f8f8f2",
                "accent": "#f92672",
                "subtitle": "#a6e22e",
                "warning": "#fd971f",
                "success": "#a6e22e",
                "error": "#f92672"
            },
            "Solarized Dark": {
                "bg": "#002b36",
                "label_fg": "#93a1a1",
                "input_bg": "#073642",
                "input_fg": "#eee8d5",
                "accent": "#b58900",
                "subtitle": "#268bd2",
                "warning": "#cb4b16",
                "success": "#859900",
                "error": "#dc322f"
            },
            "Solarized Light": {
                "bg": "#fdf6e3",
                "label_fg": "#657b83",
                "input_bg": "#eee8d5",
                "input_fg": "#657b83",
                "accent": "#b58900",
                "subtitle": "#268bd2",
                "warning": "#dc322f",
                "success": "#859900",
                "error": "#dc322f"
            }
        }
        return themes.get(theme_name, themes["Dark"])

    def apply_user_appearance(self):
        font_family = getattr(self, 'font_family', 'Segoe UI')
        font_size = int(getattr(self, 'font_size', 12))
        theme = getattr(self, 'theme', 'Dark')
        theme_colors = self.get_theme_colors(theme)

        self.root.configure(bg=theme_colors["bg"])
        self.main_container.configure(bg=theme_colors["bg"])

        self.title_frame.configure(bg=theme_colors["bg"])
        self.title_label.configure(bg=theme_colors["bg"], fg=theme_colors["accent"], font=(font_family, 28, "bold"))
        self.subtitle_label.configure(bg=theme_colors["bg"], fg=theme_colors["subtitle"], font=(font_family, 12))
        self.ai_status_label.configure(bg=theme_colors["bg"], font=(font_family, 10, "bold"))

        self.status_frame.configure(bg=theme_colors["input_bg"])
        self.status_label.configure(bg=theme_colors["input_bg"], fg=theme_colors["subtitle"], font=(font_family, 9))
        self.progress_label.configure(bg=theme_colors["input_bg"], fg=theme_colors["accent"], font=(font_family, 9))

        self.example_menu.config(
            font=(font_family, 10),
            bg=theme_colors["input_bg"],
            fg=theme_colors["input_fg"]
        )
        dropdown_menu = self.example_menu["menu"]
        dropdown_menu.config(
            font=(font_family, 10),
            bg=theme_colors["input_bg"],
            fg=theme_colors["input_fg"],
            activebackground=theme_colors["accent"],
            activeforeground=theme_colors["label_fg"]
        )

        style = ttk.Style()
        style.configure("Modern.TButton", font=(font_family, 10), background=theme_colors["accent"], foreground='white')
        style.map("Modern.TButton", background=[('active', theme_colors["accent"])])

        if hasattr(self, 'prompt_view'):
            self.prompt_view.update_appearance(font_family, font_size, theme_colors)
        if hasattr(self, 'editor_view'):
            self.editor_view.update_appearance(font_family, font_size, theme_colors)
        if hasattr(self, 'contributors_page'):
            self.contributors_page.update_appearance(font_family, font_size, theme_colors)

        self.menu_bar.config(bg=theme_colors["input_bg"], fg=theme_colors["label_fg"],
                             activebackground=theme_colors["accent"], activeforeground=theme_colors["label_fg"])
        for menu in [self.menu_bar.winfo_children()]:
            if isinstance(menu, tk.Menu):
                menu.config(bg=theme_colors["input_bg"], fg=theme_colors["label_fg"],
                            activebackground=theme_colors["accent"], activeforeground=theme_colors["label_fg"])

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        lv = len(hex_color)
        return tuple(int(hex_color[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

    def luminance(self, rgb):
        r, g, b = [x / 255.0 for x in rgb]
        a = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in (r, g, b)]
        return 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2]

    def contrast_ratio(self, color1_hex, color2_hex):
        lum1 = self.luminance(self.hex_to_rgb(color1_hex))
        lum2 = self.luminance(self.hex_to_rgb(color2_hex))
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        return (lighter + 0.05) / (darker + 0.05)

    def clear_content(self):
        for pane_widget_id in list(self.paned_window.panes()):
            self.paned_window.forget(pane_widget_id)

        self.contributors_page.pack_forget()
        self.example_menu.pack_forget()
        self.contributors_button.pack_forget()
        self.paned_window.pack_forget()
        self.status_frame.pack_forget()

    def show_contributors_page(self):
        self.clear_content()
        self.contributors_page.pack(fill='both', expand=True)
        self.update_status("Viewing contributors", "👥")

    def show_prompt_view(self):
        self.clear_content()
        self.example_var.set("🔽 Choose Example Prompt")
        self.example_menu.pack(pady=(10, 0))
        self.contributors_button.pack(pady=10)

        self.paned_window.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.prompt_view_visible.set(True)
        self.editor_view_visible.set(False)
        self.toggle_prompt_view()
        self.toggle_editor_view()

        self.status_frame.pack(fill="x", side="bottom")

        self.update_status("Ready to create amazing web experiences", "🚀")

    def show_token_manager(self):
        self.clear_content()
        token_manager_view_instance = TokenManagerView(self.main_container, self.show_prompt_view)
        token_manager_view_instance.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        token_manager_view_instance.lift()

        self.status_frame.pack(fill="x", side="bottom")

        self.update_status("GitHub Token Manager", "🔐")

    def handle_export(self):
        from exporters.exporter import export_code, export_to_github, validate_github_token
        from core.token_manager import decrypt_token

        prompt = self.prompt_view.text_input.get("1.0", "end-1c").strip()
        if not prompt:
            self.show_notification("Please enter a description", "error")
            return

        print("⚙️ Generating code...")
        code = generate_code_from_prompt(prompt)

        path = export_code(code)
        if not path:
            self.show_notification("Export cancelled", "info")
            return

        token = decrypt_token()
        if not token:
            self.show_notification("No GitHub token found. Please set up your token in GitHub > Manage Token",
                                   "warning")
            return

        is_valid, username, error = validate_github_token()
        if not is_valid:
            self.show_notification(
                f"GitHub token is invalid: {error}. Please update your token in GitHub > Manage Token", "error")
            return

        print("📤 Attempting to push to GitHub...")
        url = export_to_github(code)
        if url:
            self.show_notification(f"Pushed to GitHub: {url}", "success")
        else:
            self.show_notification("Failed to push to GitHub. Check console for details.", "error")

    def show_notification(self, message, type="info"):
        colors = {
            "info": "#58a6ff",
            "success": "#3fb950",
                "error": "#f85149",
            "warning": "#d29922",
            "error": "#f85149"
        }

        notification = tk.Toplevel(self.root)
        notification.overrideredirect(True)
        notification.attributes('-topmost', True)
        notification.configure(bg='#21262d', relief="solid", borderwidth=1)

        self.root.update_idletasks()
        x = self.root.winfo_x() + self.root.winfo_width() - 320
        y = self.root.winfo_y() + 50
        notification.geometry(f"300x80+{x}+{y}")

        tk.Label(notification, text=message, font=("Segoe UI", 10), bg='#21262d', fg=colors.get(type, "#58a6ff"),
                 wraplength=280).pack(expand=True, padx=10, pady=10)
        notification.after(3000, notification.destroy)