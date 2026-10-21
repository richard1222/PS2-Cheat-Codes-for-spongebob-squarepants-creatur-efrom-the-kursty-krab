"""File-picker interface for the private, read-only menu evidence collector."""
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import filedialog,messagebox
from collect_menu_evidence import collect

def main():
    root=tk.Tk();root.withdraw()
    try:
        source=filedialog.askopenfilename(title='Choose the original SpongeBob PS2 ISO',
            filetypes=[('PS2 ISO image','*.iso'),('All files','*.*')])
        if not source:return
        output=filedialog.asksaveasfilename(title='Save the small menu evidence ZIP',
            initialdir=str(Path(source).parent),initialfile='spongebob-menu-evidence.zip',
            defaultextension='.zip',filetypes=[('ZIP archive','*.zip')])
        if not output:return
        if Path(output).exists():
            messagebox.showerror('Choose a new filename','That output already exists. Choose a new filename to keep the existing file.');return
        root.deiconify();root.title('SpongeBob menu collector')
        tk.Label(root,text='Reading menu resources. Your ISO is not being changed.',padx=24,pady=24).pack()
        root.update()
        try:
            result=collect(source,output)
        except Exception as exc:
            root.withdraw()
            messagebox.showerror('Collection stopped',str(exc)+'\n\nPlease send this error message back in chat.')
            return
        root.withdraw()
        messagebox.showinfo('Collection complete',f"Collected {result['packages']} packages.\n\nSaved to:\n{output}\n\nUpload this ZIP privately in chat or Drive. Your ISO is unchanged.")
    finally:root.destroy()

if __name__=='__main__':main()
