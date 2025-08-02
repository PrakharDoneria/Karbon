import tkinter as tk
from tkinter import ttk, messagebox
import threading
from core.ai_engine import generate_code_from_prompt
from utils.preview import update_preview
import core.prompt_history as prompt_history
from core.ai_engine import ai_status
from core.ai_engine import optimize_prompt
from user_manager import UserManager


MAX_PROMPT_LENGTH = 256


class PromptView(tk.Frame):
    def __init__(self, master, on_generate, get_api_key_callback, get_model_source_callback, examples_data):
        super().__init__(master, bg='#0d1117')
        self.on_generate = on_generate
        self.get_api_key_callback = get_api_key_callback
        self.get_model_source_callback = get_model_source_callback
        self.examples_data = examples_data
        self.is_generating = False
        self.enhance_ui_var = tk.BooleanVar(value=True)
        self.setup_ui()
        self.bind_all("<Control-g>", lambda event: self.handle_generate())
        self.bind_all("<Control-e>", lambda event: self.export_project())
        self.bind_all("<Control-Shift-c>", lambda event: self.clear_input())

    def setup_ui(self):
        self.create_hero_section()
        self.create_input_section()
        self.create_features_section()
        self.create_examples_section()
        self.animate_elements()

    def create_hero_section(self):
        hero_frame = tk.Frame(self, bg='#0d1117')
        hero_frame.pack(fill="x", pady=(30, 20))
        self.welcome_label = tk.Label(
            hero_frame,
            text="⚡ Welcome to Karbon",
            font=("Segoe UI", 32, "bold"),
            bg='#0d1117',
            fg="#0071f3"
        )
        self.welcome_label.pack(pady=(0, 10))
        self.subtitle_label = tk.Label(
            hero_frame,
            text="",
            font=("Segoe UI", 14),
            bg='#0d1117',
            fg='#8b949e'
        )
        self.subtitle_label.pack()
        self.typewriter_text = "   Transform your ideas into stunning web experiences with AI"
        self.typewriter_index = 0
        self.typewriter_effect()

    def create_input_section(self):
        card_container = tk.Frame(self, bg='#0d1117')
        card_container.pack(fill="x", padx=50, pady=30)
        input_card = tk.Frame(card_container, bg='#161b22', relief='solid', bd=1)
        input_card.pack(fill="x")
        header_frame = tk.Frame(input_card, bg='#21262d')
        header_frame.pack(fill="x")
        tk.Label(
            header_frame,
            text="🎨 Describe Your Vision",
            font=("Segoe UI", 16, "bold"),
            bg='#21262d',
            fg='#f0f6fc',
            padx=25,
            pady=15
        ).pack(anchor="w")
        input_frame = tk.Frame(input_card, bg='#161b22')
        input_frame.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        self.text_input = tk.Text(
            input_frame,
            height=6,
            font=("Consolas", 12),
            bg='#0d1117',
            fg='#f0f6fc',
            insertbackground='#58a6ff',
            selectbackground='#264f78',
            relief='solid',
            bd=1,
            padx=20,
            pady=15,
            wrap=tk.WORD
        )
        self.text_input.pack(fill="both", expand=True, pady=(10, 15))
        self.enhance_checkbox = tk.Checkbutton(
            input_frame,
            text="Enhance prompt",
            variable=self.enhance_ui_var,
            bg="#1e1e1e",
            fg="#ffffff",
            selectcolor="#1e1e1e",
            activebackground="#1e1e1e",
            activeforeground="#00ffcc"
        )
        self.enhance_checkbox.pack(anchor="w", pady=(5, 0))
        self.char_count_label = tk.Label(
            input_frame,
            text="256 characters left",
            font=("Segoe UI", 9),
            bg='#161b22',
            fg='#8b949e',
            anchor='e'
        )
        self.char_count_label.pack(anchor="e", pady=(0, 5))
        self.text_input.bind('<KeyRelease>', self.update_char_count)
        self.text_input.bind('<Control-v>', self.update_char_count)
        self.text_input.bind('<FocusOut>', self.update_char_count)
        self.placeholder_text = "Describe your dream website... \n\nExample: Create a modern portfolio website with dark theme, smooth animations, and minimalist design"
        self.setup_placeholder()
        button_frame = tk.Frame(input_card, bg='#161b22')
        button_frame.pack(fill="x", padx=25, pady=(0, 25))
        self.generate_btn = tk.Button(
            button_frame,
            text="🚀 Generate My Website",
            font=("Segoe UI", 14, "bold"),
            bg='#238636',
            fg='white',
            activebackground='#2ea043',
            activeforeground='white',
            relief='flat',
            bd=0,
            padx=40,
            pady=15,
            cursor='hand2',
            command=self.handle_generate
        )
        self.generate_btn.pack(side="right")
        self.create_secondary_buttons(button_frame)

    def create_secondary_buttons(self, parent):
        clear_btn = tk.Button(
            parent,
            text="🗑️️ Clear",
            font=("Segoe UI", 11),
            bg='#21262d',
            fg='#8b949e',
            activebackground='#30363d',
            activeforeground='#f0f6fc',
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2',
            command=self.clear_input
        )
        clear_btn.pack(side="right", padx=(0, 15))
        random_btn = tk.Button(
            parent,
            text="🎲 Surprise Me",
            font=("Segoe UI", 11),
            bg='#6f42c1',
            fg='white',
            activebackground='#8a63d2',
            activeforeground='white',
            relief='flat',
            bd=0,
            padx=20,
            pady=10,
            cursor='hand2',
            command=self.random_idea
        )
        random_btn.pack(side="right", padx=(0, 10))

    def create_features_section(self):
        features_frame = tk.Frame(self, bg='#0d1117')
        features_frame.pack(fill="x", padx=50, pady=20)
        tk.Label(
            features_frame,
            text="✨ What Makes Karbon Special",
            font=("Segoe UI", 18, "bold"),
            bg='#0d1117',
            fg='#f0f6fc'
        ).pack(pady=(0, 20))
        features_container = tk.Frame(features_frame, bg='#0d1117')
        features_container.pack(fill="x")
        features = [
            ("🤖", "AI-Powered", "Advanced AI creates professional websites from simple descriptions"),
            ("⚡", "Lightning Fast", "Generate complete websites in seconds, not hours"),
            ("🎨", "Beautiful Design", "Modern, responsive designs that look great everywhere"),
            ("🔧", "Fully Customizable", "Edit and modify the generated code to match your vision")
        ]
        for i, (icon, title, desc) in enumerate(features):
            feature_card = tk.Frame(features_container, bg='#161b22', relief='solid', bd=1)
            feature_card.grid(row=i // 2, column=i % 2, padx=10, pady=10, sticky="ew")
            features_container.grid_columnconfigure(0, weight=1)
            features_container.grid_columnconfigure(1, weight=1)
            tk.Label(
                feature_card,
                text=icon,
                font=("Segoe UI", 24),
                bg='#161b22'
            ).pack(pady=(15, 5))
            tk.Label(
                feature_card,
                text=title,
                font=("Segoe UI", 12, "bold"),
                bg='#161b22',
                fg='#58a6ff'
            ).pack()
            tk.Label(
                feature_card,
                text=desc,
                font=("Segoe UI", 9),
                bg='#161b22',
                fg='#8b949e',
                wraplength=200,
                justify=tk.CENTER
            ).pack(pady=(5, 15), padx=15)

    def create_examples_section(self):
        examples_frame = tk.Frame(self, bg='#0d1117')
        examples_frame.pack(fill="x", padx=50, pady=20)
        tk.Label(
            examples_frame,
            text="🚀 Quick Start Ideas",
            font=("Segoe UI", 16, "bold"),
            bg='#0d1117',
            fg='#f0f6fc'
        ).pack(anchor="w", pady=(0, 15))
        examples = [
            "💼 Professional portfolio with project showcase and contact form",
            "🛍️ E-commerce store with product reviews and secure checkout",
            "📱 Mobile-first landing page with call-to-action buttons",
            "📊 Dashboard with charts and data visualization",
            "📝 Blog platform with article management and comments",
            "🍔 Restaurant website with menu and online ordering"
        ]
        for example in examples:
            example_btn = tk.Button(
                examples_frame,
                text=example,
                font=("Segoe UI", 10),
                bg='#21262d',
                fg='#8b949e',
                activebackground='#30363d',
                activeforeground='#58a6ff',
                relief='flat',
                bd=0,
                padx=20,
                pady=12,
                cursor='hand2',
                anchor='w',
                command=lambda ex=example: self.set_example(ex)
            )
            example_btn.pack(fill="x", pady=2)
            def on_enter(e, btn=example_btn):
                btn.configure(bg='#30363d', fg='#58a6ff')
            def on_leave(e, btn=example_btn):
                btn.configure(bg='#21262d', fg='#8b949e')
            example_btn.bind("<Enter>", on_enter)
            example_btn.bind("<Leave>", on_leave)

    def setup_placeholder(self):
        self.placeholder_active = True
        self.text_input.insert("1.0", self.placeholder_text)
        self.text_input.configure(fg='#6e7681')
        def on_focus_in(event):
            if self.placeholder_active:
                self.text_input.delete("1.0", "end")
                self.text_input.configure(fg='#f0f6fc')
                self.placeholder_active = False
        def on_focus_out(event):
            content = self.text_input.get("1.0", "end-1c").strip()
            if not self.text_input.get("1.0", "end-1c").strip():
                self.text_input.insert("1.0", self.placeholder_text)
                self.text_input.configure(fg='#6e7681')
                self.placeholder_active = True
        self.text_input.bind('<FocusIn>', on_focus_in)
        self.text_input.bind('<FocusOut>', on_focus_out)

    def typewriter_effect(self):
        if self.typewriter_index < len(self.typewriter_text):
            current_text = self.typewriter_text[:self.typewriter_index + 1]
            self.subtitle_label.configure(text=current_text)
            self.typewriter_index += 1
            self.after(50, self.typewriter_effect)

    def blink_cursor(self):
        current_text = self.subtitle_label.cget("text")
        if current_text.endswith("_"):
            self.subtitle_label.configure(text=current_text[:-1])
        else:
            self.subtitle_label.configure(text=current_text + "_")
        self.after(500, self.blink_cursor)

    def animate_elements(self):
        colors = ['#58a6ff', '#79c0ff', '#a5d6ff', '#79c0ff']
        color_index = [0]
        def animate_welcome():
            self.welcome_label.configure(fg=colors[color_index[0] % len(colors)])
            color_index[0] += 1
            self.after(3000, animate_welcome)
        animate_welcome()

    def set_example(self, example):
        self.text_input.delete("1.0", "end")
        clean_example = " ".join(example.split()[1:])
        self.text_input.insert("1.0", clean_example)
        self.text_input.configure(fg='#f0f6fc')
        self.placeholder_active = False
        self.update_char_count()

    def clear_input(self):
        self.text_input.delete("1.0", "end")
        self.text_input.insert("1.0", self.placeholder_text)
        self.text_input.configure(fg='#6e7681')
        self.placeholder_active = True
        self.update_char_count()

    def random_idea(self):
        import random
        templates = [
            "modern portfolio website with dark theme and smooth animations",
            "e-commerce platform with product reviews and secure checkout",
            "social media dashboard with real-time notifications",
            "food delivery app with restaurant listings and order tracking",
            "fitness tracker with workout plans and progress charts",
            "online learning platform with video courses and quizzes",
            "real estate website with property search and virtual tours",
            "music streaming app with playlists and recommendations",
            "travel booking site with hotel and flight search",
            "cryptocurrency tracker with live prices and portfolio management"
        ]
        styles = ["minimalist", "colorful", "professional", "creative", "elegant"]
        features = ["responsive design", "mobile-first approach", "accessibility features", "SEO optimization"]
        random_idea = f"Create a {random.choice(styles)} {random.choice(templates)} with {random.choice(features)}"
        self.text_input.delete("1.0", "end")
        self.text_input.insert("1.0", random_idea)
        self.text_input.configure(fg='#f0f6fc')
        self.placeholder_active = False
        self.update_char_count()

    def handle_generate(self):
        if self.is_generating:
            return
        prompt = self.text_input.get("1.0", "end-1c").strip()
        prompt = ''.join(ch for ch in prompt if ch.isprintable()).strip()
        if not prompt or prompt == self.placeholder_text:
            self.show_error("Please describe your website idea first! 💡")
            return
        if len(prompt) < 10:
            self.show_error(
                "Please provide more details about your website. The more specific you are, the better the result! 🎯")
            return
        self.start_generation(prompt)

    def start_generation(self, prompt):
        self.is_generating = True
        self.generate_btn.configure(
            text="🔄 Creating Magic...",
            state='disabled',
            bg='#6e7681'
        )
        self.show_progress()
        def generate_in_background():
            try:
                api_key = self.get_api_key_callback()
                model_source = self.get_model_source_callback()
                final_prompt = prompt
                if self.enhance_ui_var.get():
                    final_prompt = optimize_prompt(prompt, api_key)
                code = generate_code_from_prompt(final_prompt, api_key, model_source)
                try:
                    from ui_items.editor_view import HTML_AVAILABLE
                    if HTML_AVAILABLE:
                        pass
                except ImportError:
                    pass
                prompt_history.pop_prompt()
                prompt_history.push_prompt(final_prompt)
                prompt_history.push_prompt(
                    "Describe what you'd like to change...\n\nExample: Make the header purple, add a contact form or change the font to something more modern")
                prompt_history.push_code(code)
                prompt_history.push_code(code)
                self.after(0, lambda: self.generation_complete(code))
            except Exception as e:
                self.after(0, lambda exc=e: self.generation_error(str(exc)))
        threading.Thread(target=generate_in_background, daemon=True).start()

    def show_progress(self):
        progress_texts = [
            "🔄 Analyzing your idea...",
            "🎨 Designing the layout...",
            "⚡ Generating HTML & CSS...",
            "🚀 Adding interactive features...",
            "✨ Finalizing your website..."
        ]
        self.progress_index = 0
        def update_progress():
            if self.is_generating and self.progress_index < len(progress_texts):
                self.generate_btn.configure(text=progress_texts[self.progress_index])
                self.progress_index += 1
                self.after(1500, update_progress)
        update_progress()

    def generation_complete(self, code):
        self.is_generating = False
        self.generate_btn.configure(
            text="🚀 Generate My Website",
            state='normal',
            bg='#238636'
        )
        status = ai_status.get("state", "unknown")
        message = ai_status.get("message", "")
        if status != "online":
            if status == "offline":
                self.show_error(
                    "AI service is currently unavailable. Please check your internet connection or try again later.")
            elif status == "error":
                self.show_error(f"AI service error: {message}")
            else:
                self.show_error(f"Website could not be generated due to an AI service issue")
            return
        self.show_success("Website generated successfully! 🎉")
        self.on_generate(code)

    def generation_error(self, error_msg):
        self.is_generating = False
        self.generate_btn.configure(
            text="🚀 Generate My Website",
            state='normal',
            bg='#238636'
        )
        status = ai_status.get("state", "unknown")
        message = ai_status.get("message", "")
        if status == "offline":
            self.show_error(
                "AI service is currently unavailable. Please check you internet connection or try again later.")
        elif status == "error":
            self.show_error(f"AI service error: {message}")
        else:
            self.show_error(f"Oops! Something went wrong: {str(error_msg)}")

    def show_error(self, message):
        error_window = tk.Toplevel(self)
        error_window.title("Oops!")
        error_window.geometry("450x200")
        error_window.configure(bg='#21262d')
        error_window.resizable(False, False)
        error_window.transient(self.winfo_toplevel())
        error_window.grab_set()
        
        # Center the error window properly with bounds checking
        try:
            root = self.winfo_toplevel()
            root.update_idletasks()  # Ensure geometry is updated
            
            # Get screen dimensions
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            
            # Calculate center position relative to parent window
            parent_x = root.winfo_x()
            parent_y = root.winfo_y()
            parent_width = root.winfo_width()
            parent_height = root.winfo_height()
            
            # Calculate centered position
            x = parent_x + (parent_width // 2) - 225
            y = parent_y + (parent_height // 2) - 100
            
            # Ensure the window stays within screen bounds
            x = max(0, min(x, screen_width - 450))
            y = max(0, min(y, screen_height - 200))
            
            error_window.geometry(f"450x200+{x}+{y}")
        except tk.TclError:
            # Fallback to center of screen if positioning fails
            error_window.geometry("450x200+300+200")
        
        tk.Label(
            error_window,
            text="⚠️",
            font=("Segoe UI", 32),
            bg='#21262d',
            fg='#f85149'
        ).pack(pady=(20, 10))
        tk.Label(
            error_window,
            text=message,
            font=("Segoe UI", 11),
            bg='#21262d',
            fg='#f0f6fc',
            wraplength=400,
            justify=tk.CENTER
        ).pack(pady=10, padx=20)
        tk.Button(
            error_window,
            text="Got it! 👍",
            font=("Segoe UI", 11),
            bg='#238636',
            fg='white',
            relief='flat',
            padx=30,
            pady=10,
            command=error_window.destroy
        ).pack(pady=20)

    def show_success(self, message):
        success_window = tk.Toplevel(self)
        success_window.title("Success!")
        success_window.geometry("400x150")
        success_window.configure(bg='#21262d')
        success_window.resizable(False, False)
        success_window.attributes('-topmost', True)
        
        # Position the success window properly with bounds checking
        try:
            root = self.winfo_toplevel()
            root.update_idletasks()  # Ensure geometry is updated
            
            # Get screen dimensions
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            
            # Position in top-right corner of parent window
            parent_x = root.winfo_x()
            parent_y = root.winfo_y()
            parent_width = root.winfo_width()
            
            x = parent_x + parent_width - 420
            y = parent_y + 50
            
            # Ensure the window stays within screen bounds
            x = max(0, min(x, screen_width - 400))
            y = max(0, min(y, screen_height - 150))
            
            success_window.geometry(f"400x150+{x}+{y}")
        except tk.TclError:
            # Fallback positioning
            success_window.geometry("400x150+500+100")
        
        tk.Label(
            success_window,
            text="🎉",
            font=("Segoe UI", 24),
            bg='#21262d'
        ).pack(pady=(20, 5))
        tk.Label(
            success_window,
            text=message,
            font=("Segoe UI", 12),
            bg='#21262d',
            fg='#3fb950'
        ).pack(pady=5)
        success_window.after(3000, success_window.destroy)

    def update_char_count(self, event=None):
        content = self.text_input.get("1.0", "end-1c")
        if len(content) > 256:
            self.text_input.delete(f"1.0+{256}c", "end")
            content = self.text_input.get("1.0", "end-1c")
        remaining = 256 - len(content)
        self.char_count_label.config(text=f"{remaining} characters left")

    def update_appearance(self, font_family, font_size, theme_colors):
        self.welcome_label.config(font=(font_family, 32, "bold"), fg=theme_colors["accent"])
        self.subtitle_label.config(font=(font_family, 14), fg=theme_colors["subtitle"])
        self.text_input.config(
            font=("Consolas", font_size),
            bg=theme_colors["input_bg"],
            fg=theme_colors["input_fg"],
            insertbackground=theme_colors["accent"]
        )
        if self.placeholder_active:
            self.text_input.configure(fg=theme_colors["subtitle"])
        else:
            self.text_input.configure(fg=theme_colors["input_fg"])
        self.enhance_checkbox.config(
            bg=theme_colors["input_bg"],
            fg=theme_colors["label_fg"],
            selectcolor=theme_colors["input_bg"],
            activebackground=theme_colors["input_bg"],
            activeforeground=theme_colors["accent"]
        )
        self.char_count_label.config(
            font=(font_family, 9),
            bg=theme_colors["input_bg"],
            fg=theme_colors["subtitle"]
        )
        self.config(bg=theme_colors["bg"])
        for widget in self.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.config(bg=theme_colors["bg"])