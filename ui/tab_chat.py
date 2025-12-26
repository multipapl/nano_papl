import customtkinter as ctk

class TabChat(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        
        label = ctk.CTkLabel(self, text="Ad-hoc Chat - Coming Soon", font=("Arial", 20))
        label.pack(expand=True)
