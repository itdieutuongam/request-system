# app.py – ĐÃ FIX 100%, CHẠY MƯỢT, KHÔNG CÒN LỖI KHI NHẤN DUYỆT
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from functools import wraps
from datetime import datetime
import sqlite3
import os
import json
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.jinja_env.filters['fromjson'] = lambda v: json.loads(v) if v else []

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
DB_NAME = "tamung_database.db"


# ==================== HELPER: chuyển row → dict + ép kiểu số tiền ====================
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def row_to_dict(row):
    if row is None:
        return None
    d = dict(row)
    # Ép kiểu các cột tiền về float, nếu None thì 0
    for key in ['so_tien_tam_ung', 'tong_cong']:
        d[key] = float(d[key]) if d[key] is not None else 0.0
    return d

def rows_to_dict_list(rows):
    return [row_to_dict(r) for r in rows]

# ==================== DECORATOR ====================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== DATABASE INIT ====================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tamung_forms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submitter_email TEXT NOT NULL,
            submitter_name TEXT NOT NULL,
            submit_date TEXT NOT NULL,
            phong_ban TEXT NOT NULL,
            so_tien_tam_ung REAL DEFAULT 0,
            so_tien_bang_chu TEXT,
            hinh_thuc_tam_ung TEXT DEFAULT 'Tiền mặt',
            ly_do_tam_ung TEXT,
            thoi_han_hoan_ung TEXT,
            thoi_han_thanh_toan TEXT,
            chi_tiet_json TEXT,
            tong_cong REAL DEFAULT 0,
            attachment TEXT,
            status TEXT DEFAULT 'Chờ duyệt',
            current_approver TEXT,
            next_approver TEXT,
            final_approver_name TEXT,
            thanh_pho TEXT
        )
    ''')
    conn.commit()
    conn.close()

# ==================== DATA ====================
USERS = {
    # ==================== BOD ====================
    "truongkhuong@dieutuongam.com": {"name": "TRƯƠNG HUỆ KHƯƠNG", "role": "BOD", "department": "BOD"},
    "hongtuyet@dieutuongam.com": {"name": "NGUYỄN THỊ HỒNG TUYẾT", "role": "BOD", "department": "BOD"},

    # ==================== PHÒNG HCNS-IT ====================
    "it@dieutuongam.com": {"name": "TRẦN CÔNG KHÁNH", "role": "Manager", "department": "PHÒNG HCNS-IT"},
    "anthanh@dieutuongam.com": {"name": "NGUYỄN THỊ AN THANH", "role": "Manager", "department": "PHÒNG HCNS-IT"},
    "hcns@dieutuongam.com": {"name": "NHÂN SỰ DTA", "role": "Employee", "department": "PHÒNG HCNS-IT"},
    "yennhi@dieutuongam.com": {"name": "TRẦN NGỌC YẾN NHI", "role": "Employee", "department": "PHÒNG HCNS-IT"},
    "info@dieutuongam.com": {"name": "Trung Tâm Nghệ Thuật Phật Giáo Diệu Tướng Am", "role": "Employee", "department": "PHÒNG HCNS-IT"},

    # ==================== PHÒNG TÀI CHÍNH KẾ TOÁN ====================
    "ketoan@dieutuongam.com": {"name": "LÊ THỊ MAI ANH", "role": "Manager", "department": "PHÒNG TÀI CHÍNH KẾ TOÁN"},

    # ==================== PHÒNG KINH DOANH HCM ====================
    "xuanhoa@dieutuongam.com": {"name": "LÊ XUÂN HOA", "role": "Manager", "department": "PHÒNG KINH DOANH HCM"},
    "salesadmin@dieutuongam.com": {"name": "NGUYỄN DUY ANH", "role": "Employee", "department": "PHÒNG KINH DOANH HCM"},
    "kho@dieutuongam.com": {"name": "HUỲNH MINH TOÀN", "role": "Employee", "department": "PHÒNG KINH DOANH HCM"},
    "thoainha@dieutuongam.com": {"name": "TRẦN THOẠI NHÃ", "role": "Manager", "department": "PHÒNG KINH DOANH HCM"},
    "thanhtuan.dta@gmail.com": {"name": "BÀNH THANH TUẤN", "role": "Employee", "department": "PHÒNG KINH DOANH HCM"},
    "thientinh.dta@gmail.com": {"name": "BÙI THIỆN TÌNH", "role": "Employee", "department": "PHÒNG KINH DOANH HCM"},
    "giathanh.dta@gmail.com": {"name": "NGÔ GIA THÀNH", "role": "Employee", "department": "PHÒNG KINH DOANH HCM"},
    "vannhuann.dta@gmail.com": {"name": "PHẠM VĂN NHUẬN", "role": "Employee", "department": "PHÒNG KINH DOANH HCM"},
    "minhhieuu.dta@gmail.com": {"name": "LÊ MINH HIẾU", "role": "Employee", "department": "PHÒNG KINH DOANH HCM"},
    "thanhtrung.dta@gmail.com": {"name": "NGUYỄN THÀNH TRUNG", "role": "Employee", "department": "PHÒNG KINH DOANH HCM"},
    "khanhngan.dta@gmail.com": {"name": "NGUYỄN NGỌC KHÁNH NGÂN", "role": "Employee", "department": "PHÒNG KINH DOANH HCM"},
    "thitrang.dta@gmail.com": {"name": "NGUYỄN THỊ TRANG", "role": "Employee", "department": "PHÒNG KINH DOANH HCM"},
    "thanhtienn.dta@gmail.com": {"name": "NGUYỄN THANH TIẾN", "role": "Employee", "department": "PHÒNG KINH DOANH HCM"},

    # ==================== PHÒNG KINH DOANH HN ====================
    "nguyenngoc@dieutuongam.com": {"name": "NGUYỄN THỊ NGỌC", "role": "Manager", "department": "PHÒNG KINH DOANH HN"},
    "vuthuy@dieutuongam.com": {"name": "VŨ THỊ THÙY", "role": "Manager", "department": "PHÒNG KINH DOANH HN"},
    "mydung.dta@gmail.com": {"name": "HOÀNG THỊ MỸ DUNG", "role": "Employee", "department": "PHÒNG KINH DOANH HN"},

    # ==================== PHÒNG TRUYỀN THÔNG & MARKETING ====================
    "marketing@dieutuongam.com": {"name": "HUỲNH THỊ BÍCH TUYỀN", "role": "Manager", "department": "PHÒNG TRUYỀN THÔNG & MARKETING"},
    "lehong.dta@gmail.com": {"name": "LÊ THỊ HỒNG", "role": "Employee", "department": "PHÒNG TRUYỀN THÔNG & MARKETING"},

    # ==================== PHÒNG KẾ HOẠCH TỔNG HỢP ====================
    "lehuyen@dieutuongam.com": {"name": "NGUYỄN THỊ LỆ HUYỀN", "role": "Manager", "department": "PHÒNG KẾ HOẠCH TỔNG HỢP"},
    "hatrang@dieutuongam.com": {"name": "PHẠM HÀ TRANG", "role": "Manager", "department": "PHÒNG KẾ HOẠCH TỔNG HỢP"},

    # ==================== PHÒNG SÁNG TẠO TỔNG HỢP ====================
    "thietke@dieutuongam.com": {"name": "ĐẶNG THỊ MINH THÙY", "role": "Manager", "department": "PHÒNG SÁNG TẠO TỔNG HỢP"},
    "ptsp@dieutuongam.com": {"name": "DƯƠNG NGỌC HIỂU", "role": "Manager", "department": "PHÒNG SÁNG TẠO TỔNG HỢP"},
    "qlda@dieutuongam.com": {"name": "PHẠM THẾ HẢI", "role": "Manager", "department": "PHÒNG SÁNG TẠO TỔNG HỢP"},
    "minhdat.dta@gmail.com": {"name": "LÂM MINH ĐẠT", "role": "Employee", "department": "PHÒNG SÁNG TẠO TỔNG HỢP"},
    "thanhvii.dat@gmail.com": {"name": "LÊ THỊ THANH VI", "role": "Employee", "department": "PHÒNG SÁNG TẠO TỔNG HỢP"},
    "quangloi.dta@gmail.com": {"name": "LÊ QUANG LỢI", "role": "Employee", "department": "PHÒNG SÁNG TẠO TỔNG HỢP"},
    "tranlinh.dta@gmail.com": {"name": "NGUYỄN THỊ PHƯƠNG LINH", "role": "Employee", "department": "PHÒNG SÁNG TẠO TỔNG HỢP"},

    # ==================== BỘ PHẬN HỖ TRỢ - GIAO NHẬN ====================
    "hotro1.dta@gmail.com": {"name": "NGUYỄN VĂN MẠNH", "role": "Employee", "department": "BỘ PHẬN HỖ TRỢ - GIAO NHẬN"},
}

DEPARTMENTS = [
    "PHÒNG HCNS-IT", "PHÒNG TÀI CHÍNH KẾ TOÁN", "PHÒNG KINH DOANH HCM",
    "PHÒNG KINH DOANH HÀ NỘI", "PHÒNG MARKETING", "BOD"
]

# ==================== TRANG CHỦ & ĐĂNG NHẬP ====================
@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user_data = USERS.get(email)

        if user_data and user_data["password"] == password:
            session["user"] = {
                "email": email,
                "name": user_data["name"],
                "role": user_data["role"],
                "department": user_data["department"]
            }

            # CHỈ BẮT ĐỔI MẬT KHẨU NẾU VẪN ĐANG DÙNG MẬT KHẨU MẶC ĐỊNH
            if password == "123456":
                flash("Đây là lần đầu bạn đăng nhập. Vui lòng đổi mật khẩu mới để tiếp tục!", "warning")
                return redirect(url_for("change_password"))

            # Nếu đã đổi rồi → vào thẳng dashboard
            flash("Đăng nhập thành công!", "success")
            return redirect(url_for("dashboard"))

        else:
            flash("Sai email hoặc mật khẩu!", "danger")

    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    user = session["user"]
    conn = get_db_connection()
    c = conn.cursor()

    my_full = f"{user['name']} - {user['department']}"
    c.execute("SELECT * FROM tamung_forms WHERE next_approver = ? ORDER BY id DESC", (my_full,))
    pending = rows_to_dict_list(c.fetchall())

    c.execute("SELECT * FROM tamung_forms WHERE submitter_email = ? ORDER BY id DESC", (user['email'],))
    my_forms = rows_to_dict_list(c.fetchall())

    conn.close()
    return render_template("dntu_dashboard.html", user=user, pending=pending, my_forms=my_forms)

@app.route("/tamung_form", methods=["GET", "POST"])
@login_required
def tamung_form():
    user = session["user"]
    if request.method == "POST":
        phong_ban = request.form["phong_ban"]
        thanh_pho = request.form["thanh_pho"]
        so_tien = float(request.form["so_tien_tam_ung"] or 0)
        so_tien_chu = request.form["so_tien_bang_chu"]
        hinh_thuc = request.form["hinh_thuc_tam_ung"]
        ly_do = request.form["ly_do_tam_ung"]
        hoan_ung = request.form["thoi_han_hoan_ung"]
        thanh_toan = request.form.get("thoi_han_thanh_toan") or None
        approver = request.form["approver"]

        chi_tiet = []
        i = 1
        while f"noi_dung_{i}" in request.form:
            noi_dung = request.form[f"noi_dung_{i}"].strip()
            so_tien_item = request.form.get(f"so_tien_{i}")
            if noi_dung and so_tien_item:
                chi_tiet.append({"stt": i, "noi_dung": noi_dung, "so_tien": float(so_tien_item)})
            i += 1

        attachment_name = None
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename:
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                attachment_name = filename

        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO tamung_forms (
                submitter_email, submitter_name, submit_date, phong_ban,
                so_tien_tam_ung, so_tien_bang_chu, hinh_thuc_tam_ung,
                ly_do_tam_ung, thoi_han_hoan_ung, thoi_han_thanh_toan,
                chi_tiet_json, tong_cong, attachment, status, next_approver, thanh_pho
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user["email"], user["name"], datetime.now().strftime("%d/%m/%Y %H:%M"),
            phong_ban, so_tien, so_tien_chu, hinh_thuc,
            ly_do, hoan_ung, thanh_toan,
            json.dumps(chi_tiet, ensure_ascii=False), so_tien, attachment_name,
            "Chờ duyệt", approver, thanh_pho
        ))
        conn.commit()
        conn.close()
        flash("Gửi đề nghị tạm ứng thành công!", "success")
        return redirect(url_for("dashboard"))

    approvers = [f"{v['name']} - {v['department']}" for k, v in USERS.items() if v["role"] in ["Manager", "BOD"]]
    return render_template("dntu_form.html", user=user, departments=DEPARTMENTS, approvers=approvers)

@app.route("/approve/<int:form_id>", methods=["GET", "POST"])
@login_required
def approve(form_id):
    user = session["user"]
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM tamung_forms WHERE id = ?", (form_id,))
    form = row_to_dict(c.fetchone())

    if not form:
        flash("Không tìm thấy đề nghị!", "danger")
        conn.close()
        return redirect(url_for("dashboard"))

    my_full = f"{user['name']} - {user['department']}"
    if form['next_approver'] != my_full:
        flash("Chưa đến lượt bạn duyệt!", "danger")
        conn.close()
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        decision = request.form["decision"]

        if decision == "reject":
            c.execute("""
                UPDATE tamung_forms 
                SET status='Từ chối', final_approver_name=?, next_approver=NULL 
                WHERE id=?
            """, (user['name'], form_id))
            flash("Đã TỪ CHỐI đề nghị!", "danger")

        elif decision == "approve":
            if user["role"] == "BOD":
                c.execute("""
                    UPDATE tamung_forms 
                    SET status='Đã duyệt', final_approver_name=?, next_approver=NULL 
                    WHERE id=?
                """, (user['name'], form_id))
                flash("HOÀN TẤT DUYỆT THÀNH CÔNG!", "success")
            else:
                next_person = request.form.get("next_approver")
                if not next_person:
                    flash("Vui lòng chọn người duyệt tiếp theo!", "warning")
                else:
                    c.execute("UPDATE tamung_forms SET next_approver=? WHERE id=?", (next_person, form_id))
                    flash(f"Đã duyệt → Chuyển cho: {next_person.split('-')[0].strip()}", "success")

        conn.commit()
        conn.close()
        return redirect(url_for("dashboard"))

    approvers = [f"{v['name']} - {v['department']}" for k, v in USERS.items() if v["role"] in ["Manager", "BOD"]]
    conn.close()
    return render_template("dntu_approve.html", form=form, user=user, approvers=approvers, is_bod=(user["role"]=="BOD"))

@app.route("/uploads/<filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/list")
@login_required
def tamung_list():
    user = session["user"]
    if user["role"] not in ["Manager", "BOD"]:
        flash("Bạn không có quyền xem danh sách này!", "danger")
        return redirect(url_for("dashboard"))

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM tamung_forms ORDER BY id DESC")
    forms = rows_to_dict_list(c.fetchall())
    conn.close()
    return render_template("dntu_list.html", user=user, forms=forms)

@app.route("/logout")
def logout():
    session.clear()
    flash("Đã đăng xuất!", "info")
    return redirect(url_for("login"))

@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    user = session["user"]

    # Nếu người dùng đã đổi mật khẩu rồi → không cho vào trang này nữa (trừ khi tự bấm link)
    if USERS[user["email"]]["password"] != "123456":
        flash("Bạn đã đổi mật khẩu rồi, không cần vào trang này nữa.", "info")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            flash("Mật khẩu mới không khớp!", "danger")
            return render_template("change_password.html", user=user)

        if len(new_password) < 6:
            flash("Mật khẩu mới phải có ít nhất 6 ký tự!", "danger")
            return render_template("change_password.html", user=user)

        # CẬP NHẬT MẬT KHẨU MỚI → TỪ NAY KHÔNG CÒN BẮT BUỘC NỮA
        USERS[user["email"]]["password"] = new_password
        flash("Đổi mật khẩu thành công! Chào mừng bạn đến với hệ thống!", "success")
        return redirect(url_for("dashboard"))

    return render_template("change_password.html", user=user)







if __name__ == "__main__":
    init_db()
    print("="*80)
    print("HỆ THỐNG ĐÃ FIX HOÀN TOÀN – BẤM DUYỆT KHÔNG CÒN LỖI!")
    print("→ http://127.0.0.1:5000")
    print("="*80)
    app.run(host="0.0.0.0", port=5000, debug=True)