import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import shutil
import tempfile
import webbrowser
from pathlib import Path
from PIL import Image, ImageTk
import cv2
import pymupdf as fitz  # Updated PyMuPDF import

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image as RLImage
)
from xml.sax.saxutils import escape


class StudentResumeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Resume Generator - Pro Edition")
        self.root.geometry("1250x800")  # Fixed geometry specifier
        self.root.minsize(1050, 700)
        self.root.configure(bg="#eef3f8")

        self.fields = {}
        self.profile_image_path = None
        self.preview_files = set()
        self.current_temp_pdf = None
        self.preview_tk_img = None

        self.root.protocol("WM_DELETE_WINDOW", self.close_app)
        self._build_ui()
        self.update_preview()  # Initial render

    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#183153", pady=14, padx=20)
        header.pack(fill="x")
        tk.Label(
            header, text="STUDENT RESUME GENERATOR",
            font=("Segoe UI", 18, "bold"), fg="white", bg="#183153"
        ).pack(side="left")
        tk.Label(
            header, text="Interactive Desktop Studio",
            font=("Segoe UI", 10, "italic"), fg="#93c5fd", bg="#183153"
        ).pack(side="right", pady=6)

        # Main Split Container
        main_container = tk.Frame(self.root, bg="#eef3f8", padx=12, pady=12)
        main_container.pack(fill="both", expand=True)

        # Left Column: Form & Controls (Scrollable)
        left_frame = tk.Frame(main_container, bg="#eef3f8")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))

        canvas = tk.Canvas(left_frame, bg="#eef3f8", highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        form = tk.Frame(canvas, bg="white", padx=16, pady=12, relief="solid", bd=1)

        form.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=form, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(canvas_window, width=e.width))

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Right Column: In-App PDF Live Preview
        right_frame = tk.Frame(main_container, bg="white", padx=12, pady=12, relief="solid", bd=1)
        right_frame.pack(side="right", fill="both", expand=False, ipadx=10)

        tk.Label(
            right_frame, text="Live Resume Preview",
            font=("Segoe UI", 12, "bold"), fg="#183153", bg="white"
        ).pack(anchor="w", pady=(0, 8))

        # Preview Canvas Container
        preview_container = tk.Frame(right_frame, bg="#cbd5e1", width=420, height=620)
        preview_container.pack(fill="both", expand=True)
        preview_container.pack_propagate(False)

        self.preview_canvas = tk.Canvas(preview_container, bg="#e2e8f0", highlightthickness=0)
        self.preview_canvas.pack(fill="both", expand=True)

        # Preview Action Buttons
        preview_btns = tk.Frame(right_frame, bg="white", pady=10)
        preview_btns.pack(fill="x")
        tk.Button(
            preview_btns, text="🔄 Refresh Preview", command=self.update_preview,
            font=("Segoe UI", 9, "bold"), bg="#475569", fg="white",
            relief="flat", padx=10, pady=6, cursor="hand2"
        ).pack(side="left", expand=True, fill="x", padx=2)
        tk.Button(
            preview_btns, text="📥 Download PDF", command=self.download_resume,
            font=("Segoe UI", 9, "bold"), bg="#1d6f5f", fg="white",
            relief="flat", padx=10, pady=6, cursor="hand2"
        ).pack(side="right", expand=True, fill="x", padx=2)

        # Build Form Sections
        sections = [
            ("Profile Photo", [
                ("photo_section", "Profile Photo", "Upload or Capture via Webcam")
            ]),
            ("Personal Information", [
                ("full_name", "Full Name *", "e.g. Aarav Sharma"),
                ("email", "Email *", "e.g. aarav@email.com"),
                ("phone", "Phone Number *", "10-digit mobile number"),
                ("address", "Address", "City, State"),
                ("linkedin", "LinkedIn / Portfolio", "Optional"),
            ]),
            ("Education", [
                ("course", "Course / Degree *", "e.g. MCA (AI & ML)"),
                ("college", "College / University *", "College name"),
                ("graduation_year", "Passing Year", "e.g. 2028"),
                ("percentage", "Percentage / CGPA", "e.g. 89% or 8.9 CGPA"),
            ]),
            ("Skills and Experience", [
                ("skills", "Technical Skills *", "Python, SQL, HTML, CSS"),
                ("projects", "Projects", "Project name and short description"),
                ("experience", "Experience / Internship", "Write 'Fresher' if none"),
                ("certifications", "Certifications", "Optional"),
            ]),
            ("Career Objective", [
                ("objective", "Career Objective *", "A short statement about your career goal"),
            ]),
        ]

        for section_title, items in sections:
            tk.Label(
                form, text=section_title, font=("Segoe UI", 11, "bold"),
                fg="#183153", bg="white"
            ).pack(anchor="w", pady=(10, 6))

            for key, label, placeholder in items:
                if key == "photo_section":
                    photo_row = tk.Frame(form, bg="white")
                    photo_row.pack(fill="x", pady=4)
                    
                    self.photo_thumb_label = tk.Label(photo_row, bg="#e2e8f0", width=60, height=60, relief="solid", bd=1)
                    self.photo_thumb_label.pack(side="left", padx=(0, 10))
                    self._set_default_thumbnail()

                    btn_frame = tk.Frame(photo_row, bg="white")
                    btn_frame.pack(side="left", fill="x", expand=True)

                    tk.Button(
                        btn_frame, text="📁 Upload Image", command=self.upload_photo,
                        font=("Segoe UI", 9), bg="#e2e8f0", fg="#183153", relief="flat", padx=8, pady=4, cursor="hand2"
                    ).pack(side="top", anchor="w", pady=2)
                    tk.Button(
                        btn_frame, text="📷 Capture Webcam", command=self.open_webcam_dialog,
                        font=("Segoe UI", 9), bg="#e2e8f0", fg="#183153", relief="flat", padx=8, pady=4, cursor="hand2"
                    ).pack(side="top", anchor="w", pady=2)
                    continue

                row = tk.Frame(form, bg="white")
                row.pack(fill="x", pady=4)
                tk.Label(
                    row, text=label, width=20, anchor="w",
                    font=("Segoe UI", 9, "bold"), bg="white", fg="#263648"
                ).pack(side="left", anchor="nw", pady=4)

                if key in ("projects", "experience", "objective"):
                    widget = tk.Text(
                        row, height=3 if key != "objective" else 4,
                        font=("Segoe UI", 10), wrap="word",  # Integer font size
                        relief="solid", bd=1, padx=6, pady=4
                    )
                    widget.pack(side="left", fill="x", expand=True)
                else:
                    widget = tk.Entry(
                        row, font=("Segoe UI", 10), relief="solid", bd=1  # Integer font size
                    )
                    widget.pack(side="left", fill="x", expand=True, ipady=5)
                
                widget.bind("<KeyRelease>", lambda e: self.update_preview())
                self.fields[key] = widget

        # Starter Values
        self._set_value("experience", "Fresher")
        self._set_value("objective", "Motivated student seeking an opportunity to apply my skills and contribute to impactful projects.")

        # Bottom Action Bar
        bottom_bar = tk.Frame(self.root, bg="#eef3f8", pady=8, padx=12)
        bottom_bar.pack(fill="x")
        tk.Button(
            bottom_bar, text="Clear Form", command=self.clear_form,
            font=("Segoe UI", 9, "bold"), bg="#cbd5e1", fg="#183153",
            relief="flat", padx=14, pady=8, cursor="hand2"
        ).pack(side="left", padx=10)
        tk.Label(
            bottom_bar, text="* Required fields | Preview updates live as you type", bg="#eef3f8",
            fg="#64748b", font=("Segoe UI", 9)
        ).pack(side="right", padx=10)

    def _set_default_thumbnail(self):
        img = Image.new("RGB", (60, 60), color="#cbd5e1")
        self.thumb_img_tk = ImageTk.PhotoImage(img)
        self.photo_thumb_label.config(image=self.thumb_img_tk)

    def _set_value(self, key, value):
        widget = self.fields[key]
        if isinstance(widget, tk.Text):
            widget.delete("1.0", "end")
            widget.insert("1.0", value)
        else:
            widget.delete(0, "end")
            widget.insert(0, value)

    def _get_value(self, key):
        widget = self.fields[key]
        if isinstance(widget, tk.Text):
            return widget.get("1.0", "end").strip()
        return widget.get().strip()

    def upload_photo(self):
        filepath = filedialog.askopenfilename(
            title="Select Profile Photo",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp")]
        )
        if filepath:
            self.profile_image_path = filepath
            self._display_thumbnail(filepath)
            self.update_preview()

    def _display_thumbnail(self, filepath):
        try:
            img = Image.open(filepath)
            img.thumbnail((60, 60))
            self.thumb_img_tk = ImageTk.PhotoImage(img)
            self.photo_thumb_label.config(image=self.thumb_img_tk)
        except Exception as exc:
            messagebox.showerror("Image Error", f"Could not load image: {exc}")

    def open_webcam_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Capture Photo from Webcam")
        dialog.geometry("500x420")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg="#1e293b")

        tk.Label(
            dialog, text="Position yourself in front of the camera",
            font=("Segoe UI", 11, "bold"), fg="white", bg="#1e293b"
        ).pack(pady=10)

        cam_canvas = tk.Canvas(dialog, width=400, height=300, bg="black", highlightthickness=0)
        cam_canvas.pack()

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Webcam Error", "Could not open webcam device.")
            dialog.destroy()
            return

        captured_frame = [None]

        def update_frame():
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, _ = frame.shape
                min_dim = min(h, w)
                start_x = (w - min_dim) // 2
                start_y = (h - min_dim) // 2
                square = frame[start_y:start_y+min_dim, start_x:start_x+min_dim]
                
                img_resized = cv2.resize(square, (300, 300))
                captured_frame[0] = img_resized
                
                img_pil = Image.fromarray(img_resized)
                img_tk = ImageTk.PhotoImage(image=img_pil)
                cam_canvas.img_tk = img_tk
                cam_canvas.create_image(200, 150, image=img_tk)
            
            if dialog.winfo_exists():
                dialog.after(30, update_frame)

        def capture_and_save():
            if captured_frame[0] is not None:
                temp_dir = tempfile.gettempdir()
                photo_path = os.path.join(temp_dir, "webcam_capture.jpg")
                img_pil = Image.fromarray(captured_frame[0])
                img_pil.save(photo_path)
                self.profile_image_path = photo_path
                self._display_thumbnail(photo_path)
                self.update_preview()
            cap.release()
            dialog.destroy()

        update_frame()

        tk.Button(
            dialog, text="📸 Capture & Use Photo", command=capture_and_save,
            font=("Segoe UI", 10, "bold"), bg="#10b981", fg="white",
            relief="flat", padx=16, pady=8, cursor="hand2"
        ).pack(pady=10)

        dialog.protocol("WM_DELETE_WINDOW", lambda: (cap.release(), dialog.destroy()))

    def clear_form(self):
        if not messagebox.askyesno("Clear Form", "Are you sure you want to clear all fields?"):
            return
        for widget in self.fields.values():
            if isinstance(widget, tk.Text):
                widget.delete("1.0", "end")
            else:
                widget.delete(0, "end")
        self.profile_image_path = None
        self._set_default_thumbnail()
        self._set_value("experience", "Fresher")
        self._set_value(
            "objective",
            "Motivated student seeking an opportunity to apply my skills and contribute to impactful projects."
        )
        self.update_preview()

    def update_preview(self):
        data = {key: self._get_value(key) for key in self.fields}
        
        fd, temp_path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        
        try:
            self._create_pdf(data, temp_path)
            self.current_temp_pdf = temp_path
            self.preview_files.add(temp_path)
            
            doc = fitz.open(temp_path)
            page = doc.load_page(0)
            pix = page.get_pixmap(dpi=110)
            img_bytes = pix.tobytes("png")
            doc.close()

            from io import BytesIO
            img_pil = Image.open(BytesIO(img_bytes))
            
            canvas_w = self.preview_canvas.winfo_width()
            canvas_h = self.preview_canvas.winfo_height()
            if canvas_w < 50: canvas_w = 400
            if canvas_h < 50: canvas_h = 600

            img_pil.thumbnail((canvas_w, canvas_h))
            self.preview_tk_img = ImageTk.PhotoImage(img_pil)
            
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(
                canvas_w // 2, canvas_h // 2, image=self.preview_tk_img, anchor="center"
            )
        except Exception as e:
            print(f"Preview render notice: {e}")

    def download_resume(self):
        data = {key: self._get_value(key) for key in self.fields}
        if not data["full_name"]:
            messagebox.showwarning("Missing Name", "Please enter at least your Full Name to download.")
            return

        safe_name = "".join(ch for ch in data["full_name"] if ch.isalnum() or ch in (" ", "_", "-")).strip()
        default_filename = (safe_name.replace(" ", "_") or "Student") + "_Resume.pdf"

        filepath = filedialog.asksaveasfilename(
            title="Download Resume PDF",
            defaultextension=".pdf",
            initialfile=default_filename,
            filetypes=[("PDF files", "*.pdf")]
        )
        if not filepath:
            return
        try:
            shutil.copyfile(self.current_temp_pdf, filepath)
            messagebox.showinfo("Success", f"Resume downloaded successfully!\n\nSaved to:\n{filepath}")
        except OSError as exc:
            messagebox.showerror("Error", f"Could not download resume.\n\nDetails: {exc}")

    def close_app(self):
        for filepath in self.preview_files:
            try:
                os.remove(filepath)
            except OSError:
                pass
        self.root.destroy()

    def _create_pdf(self, data, filepath):
        doc = SimpleDocTemplate(
            filepath, pagesize=A4,
            rightMargin=0.55 * inch, leftMargin=0.55 * inch,
            topMargin=0.5 * inch, bottomMargin=0.5 * inch
        )
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name="StudentName", parent=styles["Title"], fontName="Helvetica-Bold",
            fontSize=21, leading=25, textColor=colors.HexColor("#183153"),
            alignment=TA_CENTER, spaceAfter=4
        ))
        styles.add(ParagraphStyle(
            name="ContactLine", parent=styles["Normal"], fontSize=8.5,
            leading=12, textColor=colors.HexColor("#526273"), alignment=TA_CENTER
        ))
        styles.add(ParagraphStyle(
            name="SectionHeader", parent=styles["Heading2"], fontName="Helvetica-Bold",
            fontSize=10.5, leading=13, textColor=colors.HexColor("#1d6f5f"),
            spaceBefore=8, spaceAfter=3
        ))
        styles.add(ParagraphStyle(
            name="ResumeBody", parent=styles["BodyText"], fontSize=9,
            leading=13, textColor=colors.HexColor("#263648"), spaceAfter=2
        ))

        def safe(value):
            return escape(value).replace("\n", "<br/>")

        story = []

        if self.profile_image_path and os.path.exists(self.profile_image_path):
            img = RLImage(self.profile_image_path, width=0.85 * inch, height=0.85 * inch)
            name_para = Paragraph(safe(data["full_name"]), styles["StudentName"])
            
            contact = [data["email"], data["phone"]]
            if data["address"]: contact.append(data["address"])
            if data["linkedin"]: contact.append(data["linkedin"])
            contact_para = Paragraph("  |  ".join(safe(x) for x in contact), styles["ContactLine"])

            header_table = Table([[img, [name_para, contact_para]]], colWidths=[1.0 * inch, 6.2 * inch])
            header_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
            ]))
            story.append(header_table)
        else:
            story.append(Paragraph(safe(data["full_name"]), styles["StudentName"]))
            contact = [data["email"], data["phone"]]
            if data["address"]: contact.append(data["address"])
            if data["linkedin"]: contact.append(data["linkedin"])
            story.append(Paragraph("  |  ".join(safe(x) for x in contact), styles["ContactLine"]))

        story.append(Spacer(1, 6))
        story.append(HRFlowable(width="100%", thickness=1.0, color=colors.HexColor("#1d6f5f")))

        def add_section(title, content):
            if content.strip():
                story.append(Paragraph(title.upper(), styles["SectionHeader"]))
                story.append(Paragraph(safe(content), styles["ResumeBody"]))

        add_section("Career Objective", data["objective"])

        if data["course"] or data["college"]:
            story.append(Paragraph("EDUCATION", styles["SectionHeader"]))
            education_rows = []
            if data["course"]:
                education_rows.append([Paragraph("<b>Course / Degree</b>", styles["ResumeBody"]), Paragraph(safe(data["course"]), styles["ResumeBody"])])
            if data["college"]:
                education_rows.append([Paragraph("<b>College / University</b>", styles["ResumeBody"]), Paragraph(safe(data["college"]), styles["ResumeBody"])])
            if data["graduation_year"]:
                education_rows.append([Paragraph("<b>Passing Year</b>", styles["ResumeBody"]), Paragraph(safe(data["graduation_year"]), styles["ResumeBody"])])
            if data["percentage"]:
                education_rows.append([Paragraph("<b>Percentage / CGPA</b>", styles["ResumeBody"]), Paragraph(safe(data["percentage"]), styles["ResumeBody"])])
            
            table = Table(education_rows, colWidths=[1.6 * inch, 5.2 * inch])
            table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f5f7")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#d7e0e5")),
            ]))
            story.append(table)

        add_section("Technical Skills", data["skills"])
        add_section("Projects", data["projects"])
        add_section("Experience / Internship", data["experience"])
        add_section("Certifications", data["certifications"])

        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=0.4, color=colors.HexColor("#d7e0e5")))
        story.append(Spacer(1, 3))
        story.append(Paragraph(
            "Resume generated using Student Resume Generator Studio",
            ParagraphStyle("Footer", parent=styles["Normal"], fontSize=7, textColor=colors.HexColor("#7b8794"), alignment=TA_CENTER)
        ))

        doc.build(story)


if __name__ == "__main__":
    root = tk.Tk()
    app = StudentResumeApp(root)
    root.mainloop()