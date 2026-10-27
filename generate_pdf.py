#!/usr/bin/env python3
"""
Professional PDF Generator for DBMS Course Submission
Formats the complete DBMS project guide and viva Q&A exactly into 'DBMS_Project_Report.pdf'
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas

PDF_FILENAME = "DBMS_Project_Report.pdf"

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Running Header on pages 2+
        if self._pageNumber > 1:
            self.drawString(54, 755, "Personal Expense Tracker — DBMS Course Project Report")
            self.drawRightString(612 - 54, 755, "Sangram Shelke | MySQL 8.0")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 747, 612 - 54, 747)

        # Running Footer on all pages
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 612 - 54, 45)
        self.drawString(54, 32, "Database Management Systems (DBMS) Mini-Project")
        self.drawRightString(612 - 54, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

def build_pdf():
    pdf_path = os.path.join(os.path.dirname(__file__), PDF_FILENAME)
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    primary = colors.HexColor("#1e3a8a")     # Deep Navy
    secondary = colors.HexColor("#0284c7")   # Tech Blue
    text_dark = colors.HexColor("#0f172a")   # Heading Dark
    text_body = colors.HexColor("#334155")   # Body Slate
    bg_light = colors.HexColor("#f8fafc")
    border_color = colors.HexColor("#cbd5e1")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=secondary,
        spaceAfter=12
    )

    sec_title_style = ParagraphStyle(
        'SecTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=primary,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    subsec_style = ParagraphStyle(
        'SubSec',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=secondary,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=text_body,
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3
    )

    q_style = ParagraphStyle(
        'Question',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13.5,
        textColor=primary,
        spaceBefore=6,
        spaceAfter=2,
        keepWithNext=True
    )

    a_style = ParagraphStyle(
        'Answer',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=text_body,
        spaceAfter=6
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("DBMS Mini-Project: Personal Expense Tracker & Financial Analytics System", title_style))
    story.append(Paragraph("Complete Project Architecture, Relational Schema, Workflow, and Viva Guide", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary, spaceAfter=10))

    meta_table_data = [
        [
            Paragraph("<b>Student / Author:</b> Sangram Shelke", body_style),
            Paragraph("<b>Database:</b> MySQL 8.0 (InnoDB) / Dual-Engine", body_style)
        ],
        [
            Paragraph("<b>Course:</b> Database Management Systems (DBMS)", body_style),
            Paragraph("<b>Framework:</b> Python (Flask) + Chart.js", body_style)
        ],
        [
            Paragraph("<b>Currency Standard:</b> Indian Rupee (INR ₹)", body_style),
            Paragraph("<b>Normalization Level:</b> Third Normal Form (3NF)", body_style)
        ]
    ]
    t_meta = Table(meta_table_data, colWidths=[250, 254])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_light),
        ('PADDING', (0,0), (-1,-1), 5),
        ('BOX', (0,0), (-1,-1), 0.5, border_color),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # SECTION 1: Technologies & Tools Used
    story.append(Paragraph("1. Technologies & Tools Used", sec_title_style))
    tech_table = [
        [Paragraph("<b>Component</b>", body_style), Paragraph("<b>Technology</b>", body_style), Paragraph("<b>Purpose</b>", body_style)],
        [Paragraph("Database (RDBMS)", body_style), Paragraph("MySQL 8.0 (with SQLite fallback)", body_style), Paragraph("Relational data storage, foreign key constraints, triggers, views, and stored procedures", body_style)],
        [Paragraph("Backend Framework", body_style), Paragraph("Python (Flask)", body_style), Paragraph("Lightweight, clean WSGI web application to execute SQL queries and serve routes", body_style)],
        [Paragraph("DB Connector", body_style), Paragraph("PyMySQL & sqlite3", body_style), Paragraph("Executes parameterized, SQL-injection-safe queries against the database", body_style)],
        [Paragraph("Frontend UI", body_style), Paragraph("HTML5, CSS3, Bootstrap 5", body_style), Paragraph("Clean, responsive dashboard layout with modals and progress bars", body_style)],
        [Paragraph("Data Visualization", body_style), Paragraph("Chart.js", body_style), Paragraph("Interactive graphical representation (Doughnut, Bar, Line, Pie)", body_style)],
        [Paragraph("Security", body_style), Paragraph("Werkzeug (PBKDF2-SHA256)", body_style), Paragraph("Cryptographic one-way hashing for user passwords", body_style)],
    ]
    t_tech = Table(tech_table, colWidths=[115, 135, 254])
    t_tech.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_tech)
    story.append(Spacer(1, 8))

    # SECTION 2: Database Concepts Implemented
    story.append(Paragraph("2. Database Concepts Implemented (From Your DBMS Syllabus)", sec_title_style))
    story.append(Paragraph("This project was built strictly adhering to core DBMS syllabus principles:", body_style))

    # 2.A Relational Schema & 3NF
    story.append(Paragraph("A. Relational Schema & 3NF Normalization", subsec_style))
    story.append(Paragraph("The database is broken down into <b>6 normalized tables</b> in Third Normal Form (3NF):", body_style))
    story.append(Paragraph("• <b>users:</b> Stores account credentials (<code>user_id</code>, <code>username</code>, <code>email</code>, <code>password_hash</code>, <code>full_name</code>, <code>currency</code>).", bullet_style))
    story.append(Paragraph("• <b>categories:</b> Stores expense categories (<code>category_id</code>, <code>user_id</code>, <code>name</code>, <code>color</code>, <code>icon</code>). Allows system default categories (<code>user_id = NULL</code>) and custom user categories.", bullet_style))
    story.append(Paragraph("• <b>payment_methods:</b> Lookup table for payment types (Cash, UPI, Credit Card, Debit Card, Net Banking).", bullet_style))
    story.append(Paragraph("• <b>expenses:</b> Core transactional table recording each transaction (<code>expense_id</code>, <code>user_id</code>, <code>category_id</code>, <code>payment_method_id</code>, <code>amount</code>, <code>expense_date</code>, <code>description</code>).", bullet_style))
    story.append(Paragraph("• <b>budgets:</b> Monthly budget thresholds per category (<code>budget_id</code>, <code>user_id</code>, <code>category_id</code>, <code>month</code>, <code>year</code>, <code>monthly_limit</code>).", bullet_style))
    story.append(Paragraph("• <b>expense_audit_logs:</b> Immutable audit log populated exclusively by database triggers.", bullet_style))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>Why is it in 3NF?</b>", subsec_style))
    story.append(Paragraph("• <b>1NF:</b> Every column has atomic (indivisible) values. No repeating comma-separated lists.", bullet_style))
    story.append(Paragraph("• <b>2NF:</b> No partial dependency. Non-key attributes depend on the full primary key.", bullet_style))
    story.append(Paragraph("• <b>3NF:</b> No transitive dependencies. For example, <code>expenses</code> stores <code>category_id</code> rather than storing the category's name, color, and icon redundantly. If a category name changes, it only updates in one place (preventing update anomalies).", bullet_style))
    story.append(Spacer(1, 4))

    # 2.B Referential Integrity & Constraints
    story.append(Paragraph("B. Referential Integrity & Constraints", subsec_style))
    story.append(Paragraph("• <b>Primary Keys (PK):</b> <code>AUTO_INCREMENT</code> unique identifiers on all tables.", bullet_style))
    story.append(Paragraph("• <b>Foreign Keys (FK) with Referential Actions:</b>", bullet_style))
    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;- <b>ON DELETE CASCADE:</b> When a user is deleted, all their expenses and budgets are safely cleaned up.", bullet_style))
    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;- <b>ON DELETE RESTRICT:</b> Prevents deleting a category if transactions are actively linked to it.", bullet_style))
    story.append(Paragraph("• <b>Check Constraints:</b> <code>CHECK (amount &gt; 0)</code> and <code>CHECK (month BETWEEN 1 AND 12)</code>.", bullet_style))
    story.append(Paragraph("• <b>Unique Constraints:</b> <code>UNIQUE (user_id, category_id, month, year)</code> on <code>budgets</code> prevents duplicate limits for the same category in the same month.", bullet_style))
    story.append(Paragraph("• <b>Performance Indexes:</b> Composite index <code>idx_expenses_user_date</code> on <code>(user_id, expense_date)</code> for fast date-range filtering, and <code>idx_expenses_category</code> on <code>(category_id)</code> for aggregation speed.", bullet_style))

    story.append(PageBreak())

    # 2.C Database Triggers
    story.append(Paragraph("C. Database Triggers (Automated Audit Trail)", subsec_style))
    story.append(Paragraph("In modern DBMS, triggers run automatically inside the database engine without needing application-level code:", body_style))
    story.append(Paragraph("• <b>trg_after_expense_insert:</b> Whenever an INSERT happens on <code>expenses</code>, the trigger automatically writes a record into <code>expense_audit_logs</code> capturing the new amount and description.", bullet_style))
    story.append(Paragraph("• <b>trg_after_expense_update:</b> When an expense is edited, the trigger captures <code>OLD.amount</code> and <code>NEW.amount</code> to track changes.", bullet_style))
    story.append(Paragraph("• <b>trg_after_expense_delete:</b> When an expense is deleted, the trigger archives the deleted transaction details.", bullet_style))
    story.append(Spacer(1, 4))

    # 2.D Database Views
    story.append(Paragraph("D. Database Views (Virtual Tables)", subsec_style))
    story.append(Paragraph("Views encapsulate complex SQL joins and aggregations:", body_style))
    story.append(Paragraph("• <b>vw_expense_details:</b> Joins <code>expenses</code>, <code>categories</code>, and <code>payment_methods</code> so the app can fetch full metadata in a single fast <code>SELECT *</code>.", bullet_style))
    story.append(Paragraph("• <b>vw_monthly_category_summary:</b> Uses <code>SUM(amount)</code> and <code>COUNT(expense_id)</code> with <code>GROUP BY</code> to provide ready-made monthly totals for the charts.", bullet_style))
    story.append(Paragraph("• <b>vw_budget_status:</b> Left joins budgets with actual monthly expenditure to compute remaining balance and percentage utilized (<code>ROUND(spent / limit * 100, 2)</code>).", bullet_style))
    story.append(Spacer(1, 8))

    # SECTION 3: How It Works
    story.append(Paragraph("3. How It Works (System Workflow)", sec_title_style))
    flow_steps = [
        ("1. User Authentication", "When a user registers, their password is encrypted using PBKDF2 hashing and stored in the <code>users</code> table along with their preferred currency (INR)."),
        ("2. Logging an Expense", "The user opens the modal, fills in the amount (₹), picks a category and payment method (e.g. UPI, Cash, Card), and submits."),
        ("3. Trigger Execution", "As soon as MySQL inserts the row into <code>expenses</code>, the trigger <code>trg_after_expense_insert</code> runs in the background and logs the event in <code>expense_audit_logs</code>."),
        ("4. Real-time Analytics", "The Dashboard and Analytics pages query the database views (<code>vw_monthly_category_summary</code>, <code>vw_budget_status</code>) to dynamically render the doughnut charts, 12-month spending trends, and budget progress bars."),
        ("5. Budget Alerts", "If spending in any category crosses 80% or 100%, the view flags it, and the dashboard turns the progress bar from green to yellow or red.")
    ]
    for step_title, step_desc in flow_steps:
        story.append(Paragraph(f"• <b>{step_title}:</b> {step_desc}", bullet_style))
    story.append(Spacer(1, 8))

    # SECTION 4: Practical Use
    story.append(Paragraph("4. What is the Practical Use of This Project?", sec_title_style))
    uses = [
        ("Personal Financial Discipline", "Helps users identify spending leaks (e.g., spending too much on dining out vs. groceries) through clear visual breakdowns."),
        ("Preventing Overspending", "Users set monthly budgets (e.g., ₹10,000 for food). The system calculates real-time remaining allowance and warns before budget breaches."),
        ("Data Integrity & Auditability", "In financial software, accidental or unauthorized changes can happen. With our DBMS triggers, every change is permanently logged with timestamps and old/new values."),
        ("Data Portability", "Users can export their financial history into CSV spreadsheets for tax preparation or offline bookkeeping.")
    ]
    for use_title, use_desc in uses:
        story.append(Paragraph(f"• <b>{use_title}:</b> {use_desc}", bullet_style))
    story.append(Spacer(1, 8))

    # SECTION 5: Viva / Exam Questions
    story.append(Paragraph("5. Top Viva / Exam Questions & Answers for Your Faculty", sec_title_style))
    viva_list = [
        ("Q1: Why did you use Views instead of writing joins in Python code?",
         "Answer: Views run directly in the database engine, allowing query optimization and pre-compilation. They simplify application code, enhance security by abstracting base tables, and allow reusable aggregations across multiple pages (dashboard, analytics, budgets)."),

        ("Q2: What is the benefit of using Database Triggers for audit logging?",
         "Answer: Triggers guarantee that audit logging occurs at the storage engine level, regardless of how the database is accessed (whether through the web app, MySQL Workbench, or a command line). It satisfies ACID properties and prevents developers from forgetting to write manual log statements in application code."),

        ("Q3: How did you ensure 3NF normalization?",
         "Answer: We eliminated partial dependencies by ensuring all non-key attributes depend on the primary key, and eliminated transitive dependencies by creating dedicated relations for categories and payment_methods and linking them via Foreign Keys."),

        ("Q4: How does the application handle referential integrity when deleting records?",
         "Answer: We applied ON DELETE CASCADE for user-owned records (so deleting an account removes their transactions), and ON DELETE RESTRICT on categories so a category cannot be accidentally deleted if historical expense records depend on it.")
    ]

    for q, a in viva_list:
        story.append(Paragraph(q, q_style))
        story.append(Paragraph(a, a_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] PDF generated at: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    build_pdf()
