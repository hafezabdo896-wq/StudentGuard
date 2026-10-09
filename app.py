import streamlit as st
import sqlite3
from datetime import date, datetime
import pandas as pd

# =========================================================
# StudentGuard
# نظام ذكي لإدارة حضور وانضباط الطلبة
# =========================================================

st.set_page_config(
    page_title="StudentGuard",
    page_icon="🎓",
    layout="wide"
)

DB = "studentguard.db"


# =========================================================
# قاعدة البيانات
# =========================================================

def get_connection():
    return sqlite3.connect(DB)


def init_db():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_no TEXT UNIQUE,
            name TEXT NOT NULL,
            grade TEXT,
            section TEXT,
            guardian TEXT,
            phone TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            event_date TEXT,
            status TEXT,
            notes TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS behaviors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            event_date TEXT,
            behavior_code TEXT,
            behavior_name TEXT,
            level TEXT,
            action TEXT,
            notes TEXT,
            FOREIGN KEY(student_id) REFERENCES students(id)
        )
    """)

    conn.commit()
    conn.close()


init_db()


# =========================================================
# بيانات المخالفات حسب اللائحة
# =========================================================

BEHAVIORS_A = {
    "A1": "الإخلال بنظام الطابور أو الحصص أو الأنشطة المدرسية أو الخروج من الصف دون استئذان",
    "A2": "عدم الالتزام بالزي المدرسي",
    "A3": "العبث بمرافق المدرسة أو وسائل النقل المدرسي",
    "A4": "الإساءة بالقول إلى أحد الزملاء",
    "A5": "عدم المحافظة على النظافة أو المظهر الشخصي",
    "A6": "عدم الالتزام بإحضار الكتب والدفاتر والأدوات المدرسية",
    "A7": "عدم مراعاة الاحترام الواجب في التعامل مع العاملين والزائرين",
    "A8": "تناول المأكولات أو المكسرات أو مضغ اللبان أو النوم أثناء الحصص",
    "A9": "عدم المحافظة على نظافة الفصل ومرافق المدرسة",
    "A10": "الإهمال في أداء الواجبات أو الأنشطة المدرسية",
    "A11": "عدم الإنصات لتوجيهات المعلم",
    "A12": "التحدث بصوت مرتفع داخل الصف الدراسي",
    "A13": "عدم الالتزام بضوابط استخدام الحافلة المدرسية"
}

BEHAVIORS_B = {
    "B1": "تزوير أحد المحتويات المدرسية",
    "B2": "تزوير توقيع ولي الأمر"
}

BEHAVIORS_C = {
    "C1": "الشجار أو تهديد الغير",
    "C2": "الاعتداء بألفاظ نابية على أحد الزملاء"
}

BEHAVIORS_D = {
    "D1": "إحضار الأجهزة السمعية والبصرية إلى المدرسة مثل الهواتف والكاميرات والمسجلات",
    "D2": "إساءة استخدام الحاسب الآلي بالمدرسة"
}


# =========================================================
# وظائف قاعدة البيانات
# =========================================================

def get_students():

    conn = get_connection()

    df = pd.read_sql_query(
        """
        SELECT id, student_no, name, grade, section, guardian, phone
        FROM students
        ORDER BY name
        """,
        conn
    )

    conn.close()

    return df


def add_student(student_no, name, grade, section, guardian, phone):

    conn = get_connection()

    try:

        conn.execute(
            """
            INSERT INTO students
            (student_no, name, grade, section, guardian, phone)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                student_no,
                name,
                grade,
                section,
                guardian,
                phone
            )
        )

        conn.commit()

        return True, "تمت إضافة الطالب بنجاح."

    except sqlite3.IntegrityError:

        return False, "رقم الطالب موجود مسبقًا."

    finally:

        conn.close()


def get_student_name(student_id):

    conn = get_connection()

    row = conn.execute(
        "SELECT name FROM students WHERE id=?",
        (student_id,)
    ).fetchone()

    conn.close()

    if row:
        return row[0]

    return ""


def count_unexcused_absence(student_id):

    conn = get_connection()

    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM attendance
        WHERE student_id=?
        AND status='غائب بدون عذر'
        """,
        (student_id,)
    ).fetchone()

    conn.close()

    return row[0]


def count_late(student_id):

    conn = get_connection()

    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM attendance
        WHERE student_id=?
        AND status='متأخر'
        """,
        (student_id,)
    ).fetchone()

    conn.close()

    return row[0]


def get_absence_action(count):

    if count >= 15:
        return (
            "إحالة إلى اللجنة",
            "إحالة موضوع الطالب إلى اللجنة لاتخاذ القرار المناسب وفق اللائحة."
        )

    if count >= 10:
        return (
            "دراسة حالة",
            "يستدعي الأمر دراسة حالة الطالب."
        )

    if count >= 8:
        return (
            "إنذار",
            "إنذار الطالب وولي أمره بالتزام قواعد الانتظام الدراسي."
        )

    if count >= 5:
        return (
            "تنبيه",
            "تنبيه الطالب وفق الإجراءات المحددة."
        )

    if count >= 2:
        return (
            "نصح",
            "تقديم النصح للطالب."
        )

    return (
        "لا إجراء إضافي",
        "لم يصل العدد إلى حد إجراء إضافي."
    )


def get_late_action(count):

    if count >= 4:
        return (
            "دراسة حالة",
            "دراسة حالة الطالب بسبب تكرار التأخر."
        )

    if count == 3:
        return (
            "إنذار",
            "إنذار الطالب وولي أمره."
        )

    if count == 2:
        return (
            "تنبيه",
            "تنبيه الطالب."
        )

    if count == 1:
        return (
            "نصح",
            "تقديم النصح للطالب."
        )

    return (
        "لا إجراء إضافي",
        "لا توجد حالة تأخر مسجلة."
    )


def get_behavior_count(student_id, behavior_code):

    conn = get_connection()

    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM behaviors
        WHERE student_id=?
        AND behavior_code=?
        """,
        (
            student_id,
            behavior_code
        )
    ).fetchone()

    conn.close()

    return row[0]


def calculate_behavior_action(student_id, code):

    count = get_behavior_count(
        student_id,
        code
    )

    # -----------------------------------------------------
    # الفئة A
    # أول مرة = نصح
    # الثانية = تنبيه
    # الثالثة = إنذار
    # الرابعة = دراسة حالة
    # -----------------------------------------------------

    if code.startswith("A"):

        if count >= 4:
            return (
                "دراسة حالة",
                count,
                "تكرار المخالفة من الفئة A للمرة الرابعة أو أكثر."
            )

        if count == 3:
            return (
                "إنذار",
                count,
                "تكرار المخالفة من الفئة A للمرة الثالثة."
            )

        if count == 2:
            return (
                "تنبيه",
                count,
                "تكرار المخالفة من الفئة A للمرة الثانية."
            )

        return (
            "نصح",
            count,
            "المخالفة من الفئة A للمرة الأولى."
        )

    # -----------------------------------------------------
    # الفئة B
    # الأولى = تنبيه
    # الثانية = إنذار
    # الثالثة = دراسة حالة
    # -----------------------------------------------------

    if code.startswith("B"):

        if count >= 3:
            return (
                "دراسة حالة",
                count,
                "تكرار المخالفة من الفئة B للمرة الثالثة أو أكثر."
            )

        if count == 2:
            return (
                "إنذار",
                count,
                "تكرار المخالفة من الفئة B للمرة الثانية."
            )

        return (
            "تنبيه",
            count,
            "المخالفة من الفئة B للمرة الأولى."
        )

    # -----------------------------------------------------
    # الفئة C
    # الأولى = إنذار
    # الثانية = دراسة حالة
    # -----------------------------------------------------

    if code.startswith("C"):

        if count >= 2:
            return (
                "دراسة حالة",
                count,
                "تكرار المخالفة من الفئة C."
            )

        return (
            "إنذار",
            count,
            "المخالفة من الفئة C للمرة الأولى."
        )

    # -----------------------------------------------------
    # الفئة D
    # فصل مؤقت لا يتجاوز 3 أيام دراسية
    # -----------------------------------------------------

    if code.startswith("D"):

        return (
            "فصل مؤقت / إجراء إداري",
            count,
            "اللائحة تنص على الفصل المؤقت لمدة لا تتجاوز ثلاثة أيام دراسية في الحالات المحددة، مع استكمال الإجراءات الإدارية."
        )

    return (
        "مراجعة إدارية",
        count,
        "تحتاج الحالة إلى مراجعة المسؤول."
    )


def add_attendance(student_id, event_date, status, notes):

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO attendance
        (student_id, event_date, status, notes)
        VALUES (?, ?, ?, ?)
        """,
        (
            student_id,
            event_date,
            status,
            notes
        )
    )

    conn.commit()
    conn.close()


def add_behavior(
    student_id,
    event_date,
    behavior_code,
    behavior_name,
    level,
    action,
    notes
):

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO behaviors
        (
            student_id,
            event_date,
            behavior_code,
            behavior_name,
            level,
            action,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            student_id,
            event_date,
            behavior_code,
            behavior_name,
            level,
            action,
            notes
        )
    )

    conn.commit()
    conn.close()


def get_student_history(student_id):

    conn = get_connection()

    attendance = pd.read_sql_query(
        """
        SELECT event_date AS التاريخ,
               status AS الحالة,
               notes AS ملاحظات
        FROM attendance
        WHERE student_id=?
        ORDER BY event_date DESC
        """,
        conn,
        params=(student_id,)
    )

    behaviors = pd.read_sql_query(
        """
        SELECT event_date AS التاريخ,
               behavior_name AS المخالفة,
               level AS الفئة,
               action AS الإجراء,
               notes AS ملاحظات
        FROM behaviors
        WHERE student_id=?
        ORDER BY event_date DESC
        """,
        conn,
        params=(student_id,)
    )

    conn.close()

    return attendance, behaviors


def get_all_behavior_records():

    conn = get_connection()

    df = pd.read_sql_query(
        """
        SELECT
            s.name AS الطالب,
            s.grade AS الصف,
            s.section AS الشعبة,
            b.event_date AS التاريخ,
            b.behavior_name AS المخالفة,
            b.level AS الفئة,
            b.action AS الإجراء,
            b.notes AS الملاحظات
        FROM behaviors b
        JOIN students s
        ON b.student_id=s.id
        ORDER BY b.event_date DESC
        """,
        conn
    )

    conn.close()

    return df


def get_all_attendance():

    conn = get_connection()

    df = pd.read_sql_query(
        """
        SELECT
            s.name AS الطالب,
            s.grade AS الصف,
            s.section AS الشعبة,
            a.event_date AS التاريخ,
            a.status AS الحالة,
            a.notes AS الملاحظات
        FROM attendance a
        JOIN students s
        ON a.student_id=s.id
        ORDER BY a.event_date DESC
        """,
        conn
    )

    conn.close()

    return df


# =========================================================
# الواجهة الجانبية
# =========================================================

st.sidebar.title("🎓 StudentGuard")

st.sidebar.write(
    "نظام إدارة الحضور والانضباط السلوكي"
)

page = st.sidebar.radio(
    "اختر القسم",
    [
        "🏠 لوحة التحكم",
        "👨‍🎓 الطلبة",
        "📅 الحضور والغياب",
        "⚠️ السلوك والمخالفات",
        "🔎 ملف الطالب",
        "📊 التقارير"
    ]
)


# =========================================================
# لوحة التحكم
# =========================================================

if page == "🏠 لوحة التحكم":

    st.title("🎓 StudentGuard")
    st.subheader(
        "نظام ذكي لإدارة حضور وانضباط الطلبة"
    )

    st.info(
        "يقوم النظام بتسجيل البيانات وتحليلها "
        "وعرض الإجراء المستحق وفق القواعد المبرمجة "
        "من لائحة شؤون الطلبة."
    )

    students_df = get_students()
    attendance_df = get_all_attendance()
    behavior_df = get_all_behavior_records()

    total_students = len(students_df)

    total_absence = 0

    if not attendance_df.empty:

        total_absence = len(
            attendance_df[
                attendance_df["الحالة"] == "غائب بدون عذر"
            ]
        )

    total_late = 0

    if not attendance_df.empty:

        total_late = len(
            attendance_df[
                attendance_df["الحالة"] == "متأخر"
            ]
        )

    total_behavior = len(behavior_df)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "👨‍🎓 الطلبة",
            total_students
        )

    with col2:
        st.metric(
            "🚫 غياب بدون عذر",
            total_absence
        )

    with col3:
        st.metric(
            "⏰ حالات التأخر",
            total_late
        )

    with col4:
        st.metric(
            "⚠️ المخالفات",
            total_behavior
        )

    st.markdown("---")

    st.write("## 🧠 فكرة النظام")

    st.markdown(
        """
        **البيانات → التحليل → مقارنة باللائحة → توصية بالإجراء → اعتماد المسؤول**

        النظام لا يصدر قرار الفصل أو العقوبة بصورة آلية،
        وإنما يساعد الجهة المختصة على معرفة الإجراء
        الذي تستدعيه البيانات وفق اللائحة.
        """
    )


# =========================================================
# الطلبة
# =========================================================

elif page == "👨‍🎓 الطلبة":

    st.title("👨‍🎓 إدارة الطلبة")

    with st.expander("➕ إضافة طالب جديد", expanded=True):

        col1, col2 = st.columns(2)

        with col1:

            student_no = st.text_input(
                "رقم الطالب"
            )

            name = st.text_input(
                "اسم الطالب"
            )

            grade = st.text_input(
                "الصف"
            )

        with col2:

            section = st.text_input(
                "الشعبة"
            )

            guardian = st.text_input(
                "اسم ولي الأمر"
            )

            phone = st.text_input(
                "هاتف ولي الأمر"
            )

        if st.button(
            "💾 حفظ الطالب",
            use_container_width=True
        ):

            if name.strip() == "":

                st.error(
                    "يجب إدخال اسم الطالب."
                )

            else:

                ok, message = add_student(
                    student_no,
                    name,
                    grade,
                    section,
                    guardian,
                    phone
                )

                if ok:
                    st.success(message)
                else:
                    st.error(message)

    st.markdown("---")

    st.write("## 📋 قائمة الطلبة")

    df = get_students()

    if df.empty:

        st.info(
            "لا توجد بيانات طلبة حتى الآن."
        )

    else:

        display = df.rename(
            columns={
                "student_no": "رقم الطالب",
                "name": "الاسم",
                "grade": "الصف",
                "section": "الشعبة",
                "guardian": "ولي الأمر",
                "phone": "الهاتف"
            }
        )

        st.dataframe(
            display.drop(columns=["id"]),
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# الحضور والغياب
# =========================================================

elif page == "📅 الحضور والغياب":

    st.title("📅 الحضور والغياب")

    students = get_students()

    if students.empty:

        st.warning(
            "أضف الطلاب أولًا من قسم الطلبة."
        )

    else:

        student_options = {
            f"{row['student_no']} — {row['name']}":
            row["id"]
            for _, row in students.iterrows()
        }

        selected = st.selectbox(
            "اختر الطالب",
            list(student_options.keys())
        )

        student_id = student_options[selected]

        event_date = st.date_input(
            "التاريخ",
            value=date.today()
        )

        status = st.selectbox(
            "حالة الطالب",
            [
                "حاضر",
                "غائب بعذر",
                "غائب بدون عذر",
                "متأخر"
            ]
        )

        notes = st.text_area(
            "ملاحظات"
        )

        if st.button(
            "💾 تسجيل الحالة",
            use_container_width=True
        ):

            add_attendance(
                student_id,
                str(event_date),
                status,
                notes
            )

            st.success(
                "تم تسجيل الحالة بنجاح."
            )

            # تحليل فوري

            if status == "غائب بدون عذر":

                count = count_unexcused_absence(
                    student_id
                )

                action, explanation = get_absence_action(
                    count
                )

                st.markdown("---")

                st.write("## 🧠 تحليل النظام")

                st.metric(
                    "عدد أيام الغياب بدون عذر",
                    count
                )

                if count >= 15:

                    st.error(
                        f"🚨 {action}"
                    )

                elif count >= 10:

                    st.warning(
                        f"⚠️ {action}"
                    )

                elif count >= 5:

                    st.warning(
                        f"⚠️ {action}"
                    )

                else:

                    st.info(
                        f"ℹ️ {action}"
                    )

                st.write(
                    explanation
                )

            elif status == "متأخر":

                count = count_late(
                    student_id
                )

                action, explanation = get_late_action(
                    count
                )

                st.markdown("---")

                st.write("## 🧠 تحليل التأخر")

                st.metric(
                    "عدد مرات التأخر",
                    count
                )

                st.warning(
                    f"الإجراء المقترح: {action}"
                )

                st.write(
                    explanation
                )

        st.markdown("---")

        st.write("## 📋 سجل الحضور")

        attendance, _ = get_student_history(
            student_id
        )

        if attendance.empty:

            st.info(
                "لا توجد سجلات لهذا الطالب."
            )

        else:

            st.dataframe(
                attendance,
                use_container_width=True,
                hide_index=True
            )


# =========================================================
# السلوك والمخالفات
# =========================================================

elif page == "⚠️ السلوك والمخالفات":

    st.title("⚠️ السلوك والانضباط")

    students = get_students()

    if students.empty:

        st.warning(
            "أضف الطلاب أولًا."
        )

    else:

        student_options = {
            f"{row['student_no']} — {row['name']}":
            row["id"]
            for _, row in students.iterrows()
        }

        selected = st.selectbox(
            "اختر الطالب",
            list(student_options.keys())
        )

        student_id = student_options[selected]

        event_date = st.date_input(
            "تاريخ المخالفة",
            value=date.today()
        )

        category = st.selectbox(
            "نوع المخالفة",
            [
                "الفئة A — مخالفات السلوك اليومية",
                "الفئة B — مخالفات محددة",
                "الفئة C — الشجار والاعتداء اللفظي",
                "الفئة D — أجهزة/حاسب"
            ]
        )

        if category.startswith("الفئة A"):

            options = BEHAVIORS_A
            level = "A"

        elif category.startswith("الفئة B"):

            options = BEHAVIORS_B
            level = "B"

        elif category.startswith("الفئة C"):

            options = BEHAVIORS_C
            level = "C"

        else:

            options = BEHAVIORS_D
            level = "D"

        code = st.selectbox(
            "حدد المخالفة",
            list(options.keys()),
            format_func=lambda x:
                f"{x} — {options[x]}"
        )

        behavior_name = options[code]

        notes = st.text_area(
            "تفاصيل أو ملاحظات إضافية"
        )

        action, previous_count, explanation = calculate_behavior_action(
            student_id,
            code
        )

        st.markdown("---")

        st.write("## 🧠 تحليل اللائحة")

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "عدد مرات هذه المخالفة سابقًا",
                previous_count
            )

        with col2:

            st.metric(
                "الإجراء المقترح",
                action
            )

        st.info(
            explanation
        )

        if action == "دراسة حالة":

            st.warning(
                "⚠️ هذه الحالة تستدعي دراسة حالة "
                "وفق التسلسل المحدد في اللائحة."
            )

        elif action.startswith("فصل"):

            st.error(
                "🚨 الحالة تدخل في نطاق الفصل المؤقت "
                "المحدد في اللائحة. القرار النهائي من اختصاص الجهة المدرسية المختصة."
            )

        if st.button(
            "💾 تسجيل المخالفة",
            use_container_width=True
        ):

            add_behavior(
                student_id,
                str(event_date),
                code,
                behavior_name,
                level,
                action,
                notes
            )

            st.success(
                "تم تسجيل المخالفة وتحليلها."
            )

            st.info(
                f"الإجراء المقترح: {action}"
            )


# =========================================================
# ملف الطالب
# =========================================================

elif page == "🔎 ملف الطالب":

    st.title("🔎 الملف السلوكي والدراسي للطالب")

    students = get_students()

    if students.empty:

        st.warning(
            "لا توجد بيانات طلبة."
        )

    else:

        student_options = {
            f"{row['student_no']} — {row['name']}":
            row["id"]
            for _, row in students.iterrows()
        }

        selected = st.selectbox(
            "اختر الطالب",
            list(student_options.keys())
        )

        student_id = student_options[selected]

        attendance, behaviors = get_student_history(
            student_id
        )

        absence_count = count_unexcused_absence(
            student_id
        )

        late_count = count_late(
            student_id
        )

        behavior_count = len(behaviors)

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "غياب بدون عذر",
                absence_count
            )

        with col2:

            st.metric(
                "مرات التأخر",
                late_count
            )

        with col3:

            st.metric(
                "المخالفات",
                behavior_count
            )

        absence_action, _ = get_absence_action(
            absence_count
        )

        late_action, _ = get_late_action(
            late_count
        )

        st.markdown("---")

        st.write("## 🚦 حالة الطالب")

        if absence_count >= 15:

            st.error(
                "🚨 الغياب وصل إلى مرحلة الإحالة للجنة."
            )

        elif absence_count >= 10:

            st.warning(
                "⚠️ الغياب وصل إلى مرحلة دراسة الحالة."
            )

        elif absence_count >= 8:

            st.warning(
                "⚠️ الطالب في مرحلة الإنذار بسبب الغياب."
            )

        elif absence_count >= 5:

            st.info(
                "ℹ️ الطالب في مرحلة التنبيه بسبب الغياب."
            )

        elif absence_count >= 2:

            st.info(
                "ℹ️ الطالب يحتاج إلى نصح بسبب الغياب."
            )

        else:

            st.success(
                "✅ لا توجد حالة غياب تستدعي إجراءً إضافيًا."
            )

        st.write(
            f"**إجراء الغياب الحالي:** {absence_action}"
        )

        st.write(
            f"**إجراء التأخر الحالي:** {late_action}"
        )

        st.markdown("---")

        st.write("## 📅 سجل الحضور والغياب")

        if attendance.empty:

            st.info(
                "لا يوجد سجل حضور."
            )

        else:

            st.dataframe(
                attendance,
                use_container_width=True,
                hide_index=True
            )

        st.markdown("---")

        st.write("## ⚠️ سجل المخالفات")

        if behaviors.empty:

            st.info(
                "لا توجد مخالفات مسجلة."
            )

        else:

            st.dataframe(
                behaviors,
                use_container_width=True,
                hide_index=True
            )


# =========================================================
# التقارير
# =========================================================

elif page == "📊 التقارير":

    st.title("📊 التقارير")

    tab1, tab2 = st.tabs(
        [
            "📅 تقرير الحضور",
            "⚠️ تقرير المخالفات"
        ]
    )

    with tab1:

        attendance = get_all_attendance()

        if attendance.empty:

            st.info(
                "لا توجد بيانات حضور."
            )

        else:

            st.dataframe(
                attendance,
                use_container_width=True,
                hide_index=True
            )

            csv = attendance.to_csv(
                index=False
            ).encode("utf-8-sig")

            st.download_button(
                "⬇️ تحميل تقرير الحضور",
                csv,
                "attendance_report.csv",
                "text/csv"
            )

    with tab2:

        behaviors = get_all_behavior_records()

        if behaviors.empty:

            st.info(
                "لا توجد مخالفات."
            )

        else:

            st.dataframe(
                behaviors,
                use_container_width=True,
                hide_index=True
            )

            csv = behaviors.to_csv(
                index=False
            ).encode("utf-8-sig")

            st.download_button(
                "⬇️ تحميل تقرير المخالفات",
                csv,
                "behavior_report.csv",
                "text/csv"
            )


# =========================================================
# نهاية البرنامج
# =========================================================

st.sidebar.markdown("---")

st.sidebar.caption(
    "StudentGuard — نظام دعم قرار مدرسي"
)

st.sidebar.caption(
    "القرار النهائي في الإجراءات التأديبية "
    "من اختصاص الجهة المدرسية المختصة."
)
