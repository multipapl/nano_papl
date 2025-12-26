import customtkinter as ctk
from ui.tab_constructor import TabConstructor
from ui.tab_batch import TabBatch
from ui.tab_chat import TabChat
from utils import config_helper

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class NanoPaplApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Nano Papl | AI Archviz Automation")
        self.geometry("1200x900")

        # Load global config if needed for window position etc.
        # layout configuration could be added here later

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tabview.add("Constructor")
        self.tabview.add("Batch Studio")
        self.tabview.add("Ad-hoc Chat")

        # Initialize Tabs
        self.tab_constructor = TabConstructor(self.tabview.tab("Constructor"))
        self.tab_constructor.pack(fill="both", expand=True)

        self.tab_batch = TabBatch(self.tabview.tab("Batch Studio"))
        self.tab_batch.pack(fill="both", expand=True)

        self.tab_chat = TabChat(self.tabview.tab("Ad-hoc Chat"))
        self.tab_chat.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = NanoPaplApp()
    app.mainloop()
