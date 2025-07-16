import tkinter as tk

def clicked():
    print("Clicked!")

root = tk.Tk()
tk.Button(root, text="Click me", command=clicked).pack()
root.mainloop()
