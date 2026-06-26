import customtkinter as ctk
from gui.login_window import abrir_login
from gui.main_window import MainWindow 

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

DEV_MODE = False

if __name__ == "__main__":
    if DEV_MODE:
        print("🔧 Modo Desarrollo Activo: Saltando Login")
        
        usuario = "veronica"
        jerarquia = "admin"  
        
        MainWindow(usuario, jerarquia).mainloop()
        
    else:
        # Flujo normal de producción
        abrir_login()