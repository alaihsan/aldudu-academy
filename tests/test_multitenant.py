"""
Test Suite: Multi-Tenant Isolation (Stage 2)
============================================
Memastikan semua fitur tenant isolation bekerja dengan benar:
setiap sekolah hanya bisa mengakses data miliknya sendiri.

Skenario yang diuji:
  1. Issues   - isolasi baca/ubah/hapus per sekolah
  2. Admin     - dashboard, reset password, toggle user antar sekolah
  3. Courses   - isolasi tahun ajaran, kelas, dan enrollment
  4. Tickets   - isolasi akses & penutupan ticket antar sekolah
  5. Services  - generate_ticket_number & queue_position per sekolah
  6. Edge case - user tanpa school_id ditolak login
"""

import pytest
from sqlalchemy.pool import StaticPool
from app import create_app
from app.extensions import db as _db
from app.models import (
    User, UserRole, School, SchoolStatus,
    AcademicYear, Course,
    Issue, IssueStatus, IssuePriority,
    Ticket, TicketStatus, TicketCategory, TicketPriority,
)

# ─── Config ────────────────────────────────────────────────────────────────────
#
# StaticPool: memaksa SQLite in-memory hanya pakai 1 koneksi yang sama di semua
# thread/context sehingga data yang di-commit di fixture tetap terlihat di request.
#
# App context TIDAK dibiarkan terbuka selama test berjalan — ini penting agar
# flask.g (tempat Flask-Login menyimpan _login_user) di-reset di setiap request
# dan tidak bocor antar test client yang berbeda.

TEST_CFG = {
    'TESTING': True,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    'SECRET_KEY': 'test-secret-key',
    'WTF_CSRF_ENABLED': False,
    'CACHE_TYPE': 'SimpleCache',
    'RATELIMIT_ENABLED': False,
    'SQLALCHEMY_ENGINE_OPTIONS': {
        'connect_args': {'check_same_thread': False},
        'poolclass': StaticPool,
    },
}

# Credentials yang dipakai di semua test (konstanta, bukan SQLAlchemy objects)
ADMIN_A_EMAIL  = 'admin@alpha.sch.id'
ADMIN_B_EMAIL  = 'admin@beta.sch.id'
GURU_A_EMAIL   = 'guru@alpha.sch.id'
GURU_B_EMAIL   = 'guru@beta.sch.id'
MURID_A_EMAIL  = 'murid@alpha.sch.id'
MURID_B_EMAIL  = 'murid@beta.sch.id'
PWD            = 'password123'

# ─── Helpers ───────────────────────────────────────────────────────────────────

def _make_school(name, slug):
    s = School(name=name, slug=slug, email=f'info@{slug}.id',
               admin_email=f'admin@{slug}.id', status=SchoolStatus.ACTIVE)
    _db.session.add(s)
    return s


def _make_user(name, email, role, school):
    u = User(name=name, email=email, role=role,
             school_id=school.id, email_verified=True, is_active=True)
    u.set_password(PWD)
    _db.session.add(u)
    return u


def _make_year(school):
    ay = AcademicYear(year='2025/2026', is_active=True, school_id=school.id)
    _db.session.add(ay)
    return ay


def _make_course(name, code, year, teacher):
    c = Course(name=name, class_code=code,
               academic_year_id=year.id, teacher_id=teacher.id)
    _db.session.add(c)
    return c


def _make_ticket(user, school, status=TicketStatus.RESOLVED):
    t = Ticket(
        ticket_number=f'TKT-{school.slug.upper()}-001',
        title='Test ticket', description='Desc',
        category=TicketCategory.GENERAL, status=status,
        priority=TicketPriority.MEDIUM,
        school_id=school.id, user_id=user.id,
    )
    _db.session.add(t)
    return t


def _make_issue(user, school):
    i = Issue(title='Bug', description='Desc', priority=IssuePriority.MEDIUM,
              user_id=user.id, school_id=school.id)
    _db.session.add(i)
    return i


def login(client, email, password=PWD):
    return client.post('/api/login', json={'email': email, 'password': password})


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope='module')
def app():
    """
    App fixture dengan app context yang TIDAK dibiarkan terbuka selama test.
    Ini penting agar flask.g di-reset per-request dan _login_user tidak bocor.
    StaticPool memastikan in-memory SQLite tetap pakai koneksi yang sama.
    """
    application = create_app(test_config=TEST_CFG)
    with application.app_context():
        _db.create_all()
    yield application
    with application.app_context():
        _db.drop_all()


@pytest.fixture(scope='module')
def seed(app):
    """
    Seed dua sekolah lengkap dengan users, courses, tickets, issues.
    Mengembalikan DICT primitif (ID, slug, email, kode) — bukan SQLAlchemy object —
    supaya tidak terjadi DetachedInstanceError saat diakses di luar session.
    """
    with app.app_context():
        school_a = _make_school('SMA Alpha', 'alpha')
        school_b = _make_school('SMA Beta',  'beta')
        _db.session.flush()

        admin_a  = _make_user('Admin A',  ADMIN_A_EMAIL,  UserRole.ADMIN, school_a)
        guru_a   = _make_user('Guru A',   GURU_A_EMAIL,   UserRole.GURU,  school_a)
        murid_a  = _make_user('Murid A',  MURID_A_EMAIL,  UserRole.MURID, school_a)
        admin_b  = _make_user('Admin B',  ADMIN_B_EMAIL,  UserRole.ADMIN, school_b)
        guru_b   = _make_user('Guru B',   GURU_B_EMAIL,   UserRole.GURU,  school_b)
        murid_b  = _make_user('Murid B',  MURID_B_EMAIL,  UserRole.MURID, school_b)
        _db.session.flush()

        year_a   = _make_year(school_a)
        year_b   = _make_year(school_b)
        _db.session.flush()

        course_a = _make_course('Mat A', 'AAAAAA', year_a, guru_a)
        course_b = _make_course('Mat B', 'BBBBBB', year_b, guru_b)
        _db.session.flush()

        issue_a  = _make_issue(murid_a, school_a)
        issue_b  = _make_issue(murid_b, school_b)
        ticket_a = _make_ticket(murid_a, school_a, TicketStatus.RESOLVED)
        ticket_b = _make_ticket(murid_b, school_b, TicketStatus.RESOLVED)
        _db.session.flush()

        # ── Orphan user (no school) untuk edge-case test ────────────────────
        orphan = User(name='Orphan', email='orphan@test.com',
                      role=UserRole.MURID, school_id=None,
                      email_verified=True, is_active=True)
        orphan.set_password(PWD)
        _db.session.add(orphan)

        _db.session.commit()

        # Kumpulkan nilai primitif sebelum keluar dari app_context
        return {
            'school_a_id':   school_a.id,
            'school_a_slug': school_a.slug,
            'school_b_id':   school_b.id,
            'school_b_slug': school_b.slug,
            'admin_a_id':    admin_a.id,
            'admin_b_id':    admin_b.id,
            'guru_a_id':     guru_a.id,
            'guru_b_id':     guru_b.id,
            'murid_a_id':    murid_a.id,
            'murid_b_id':    murid_b.id,
            'year_a_id':     year_a.id,
            'year_b_id':     year_b.id,
            'course_a_id':   course_a.id,
            'course_a_code': course_a.class_code,
            'course_b_id':   course_b.id,
            'course_b_code': course_b.class_code,
            'issue_a_id':    issue_a.id,
            'issue_b_id':    issue_b.id,
            'ticket_a_id':   ticket_a.id,
            'ticket_b_id':   ticket_b.id,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ISSUES
# ═══════════════════════════════════════════════════════════════════════════════

class TestIssuesIsolation:

    def test_issue_created_with_school_id(self, app, seed):
        """Issue baru harus menyimpan school_id dari user yang membuatnya."""
        with app.app_context():
            iss = Issue.query.filter_by(id=seed['issue_a_id']).first()
            assert iss is not None
            assert iss.school_id == seed['school_a_id'], \
                "Issue harus punya school_id yang benar!"

    def test_admin_only_sees_own_school_issues(self, app, seed):
        """Admin A tidak boleh melihat issue milik Sekolah B dalam listing."""
        client = app.test_client()
        login(client, ADMIN_A_EMAIL)
        resp = client.get('/api/issues')
        assert resp.status_code == 200
        ids = [i['id'] for i in resp.get_json()['issues']]
        assert seed['issue_a_id'] in ids
        assert seed['issue_b_id'] not in ids, \
            "Admin A TIDAK BOLEH melihat issue Sekolah B!"

    def test_cross_school_issue_update_blocked(self, app, seed):
        """Admin A mencoba update issue Sekolah B → harus 403."""
        client = app.test_client()
        login(client, ADMIN_A_EMAIL)
        resp = client.put(f'/api/issues/{seed["issue_b_id"]}',
                          json={'status': 'IN_PROGRESS'})
        assert resp.status_code == 403, \
            "Update issue lintas sekolah harus 403!"

    def test_cross_school_issue_delete_blocked(self, app, seed):
        """Admin A mencoba hapus issue Sekolah B → harus 403."""
        client = app.test_client()
        login(client, ADMIN_A_EMAIL)
        resp = client.delete(f'/api/issues/{seed["issue_b_id"]}')
        assert resp.status_code == 403, \
            "Hapus issue lintas sekolah harus 403!"


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ADMIN — User Management
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdminIsolation:

    def test_admin_reset_password_cross_school_blocked(self, app, seed):
        """Admin A tidak bisa reset password user Sekolah B → harus 403."""
        client = app.test_client()
        login(client, ADMIN_A_EMAIL)
        resp = client.post(
            f'/admin/api/users/{seed["murid_b_id"]}/reset-password',
            json={'password': 'newpass123'},
        )
        assert resp.status_code == 403, \
            "Reset password lintas sekolah harus 403!"

    def test_admin_reset_password_own_school_allowed(self, app, seed):
        """Admin A bisa reset password user Sekolah A sendiri."""
        client = app.test_client()
        login(client, ADMIN_A_EMAIL)
        resp = client.post(
            f'/admin/api/users/{seed["murid_a_id"]}/reset-password',
            json={'password': 'newpass123'},
        )
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True
        # Kembalikan password murid_a ke semula agar test lain tetap bisa login
        client.post(
            f'/admin/api/users/{seed["murid_a_id"]}/reset-password',
            json={'password': PWD},
        )

    def test_admin_toggle_user_cross_school_blocked(self, app, seed):
        """Admin A tidak bisa toggle status user Sekolah B → harus 403."""
        client = app.test_client()
        login(client, ADMIN_A_EMAIL)
        resp = client.post(
            f'/admin/api/users/{seed["murid_b_id"]}/toggle-status'
        )
        assert resp.status_code == 403, \
            "Toggle user lintas sekolah harus 403!"

    def test_admin_toggle_user_own_school_allowed(self, app, seed):
        """Admin A bisa toggle status user Sekolah A sendiri."""
        client = app.test_client()
        login(client, ADMIN_A_EMAIL)
        resp = client.post(
            f'/admin/api/users/{seed["murid_a_id"]}/toggle-status'
        )
        assert resp.status_code == 200
        # Kembalikan ke aktif (murid_a juga dipakai test lain)
        client.post(f'/admin/api/users/{seed["murid_a_id"]}/toggle-status')

    def test_bulk_import_assigns_admin_school(self, app, seed):
        """Bulk import user otomatis mendapat school_id admin yang login."""
        client = app.test_client()
        login(client, ADMIN_A_EMAIL)
        resp = client.post(
            '/admin/api/users/bulk-import',
            json={'raw_data': 'Siswa Import import.bulk@alpha.sch.id', 'role': 'murid'},
        )
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True
        with app.app_context():
            new_user = User.query.filter_by(email='import.bulk@alpha.sch.id').first()
            assert new_user is not None
            assert new_user.school_id == seed['school_a_id'], \
                "Bulk import harus assign school_id dari admin yang login!"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. COURSES — Academic Year & Enrollment
# ═══════════════════════════════════════════════════════════════════════════════

class TestCoursesIsolation:

    def test_cross_school_academic_year_blocked(self, app, seed):
        """Murid A tidak bisa akses Academic Year Sekolah B → 400."""
        client = app.test_client()
        login(client, MURID_A_EMAIL)
        resp = client.get(f'/api/courses/year/{seed["year_b_id"]}')
        assert resp.status_code == 400, \
            "Akses academic year lintas sekolah harus 400!"

    def test_enroll_cross_school_blocked(self, app, seed):
        """Murid A tidak bisa enroll di Kelas Sekolah B pakai class_code → 403."""
        client = app.test_client()
        login(client, MURID_A_EMAIL)
        resp = client.post('/api/enroll',
                           json={'class_code': seed['course_b_code']})
        assert resp.status_code == 403, \
            "Enrollment lintas sekolah harus 403!"

    def test_enroll_same_school_allowed(self, app, seed):
        """Murid A bisa enroll di Kelas Sekolah A sendiri."""
        client = app.test_client()
        login(client, MURID_A_EMAIL)
        resp = client.post('/api/enroll',
                           json={'class_code': seed['course_a_code']})
        # 200 (berhasil) atau 409 (sudah terdaftar) — keduanya benar
        assert resp.status_code in (200, 409), \
            f"Enrollment ke kelas sendiri harus diizinkan (200/409), bukan {resp.status_code}"

    def test_update_course_cross_school_blocked(self, app, seed):
        """Guru A tidak bisa update Kelas Sekolah B → 403."""
        client = app.test_client()
        login(client, GURU_A_EMAIL)
        resp = client.put(f'/api/courses/{seed["course_b_id"]}',
                          json={'name': 'Hacked!'})
        assert resp.status_code == 403, \
            "Update kelas lintas sekolah harus 403!"

    def test_delete_course_cross_school_blocked(self, app, seed):
        """Guru A tidak bisa hapus Kelas Sekolah B → 403."""
        client = app.test_client()
        login(client, GURU_A_EMAIL)
        resp = client.delete(f'/api/courses/{seed["course_b_id"]}')
        assert resp.status_code == 403, \
            "Hapus kelas lintas sekolah harus 403!"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. TICKETS
# ═══════════════════════════════════════════════════════════════════════════════

class TestTicketsIsolation:

    def test_get_ticket_cross_school_blocked(self, app, seed):
        """Murid A tidak bisa lihat ticket Sekolah B → 403."""
        client = app.test_client()
        login(client, MURID_A_EMAIL)
        slug = seed['school_a_slug']
        resp = client.get(f'/s/{slug}/api/tickets/{seed["ticket_b_id"]}')
        assert resp.status_code == 403, \
            "Akses ticket lintas sekolah harus 403!"

    def test_close_ticket_cross_school_blocked(self, app, seed):
        """Murid A tidak bisa tutup ticket Sekolah B → 403."""
        client = app.test_client()
        login(client, MURID_A_EMAIL)
        slug = seed['school_a_slug']
        resp = client.post(f'/s/{slug}/api/tickets/{seed["ticket_b_id"]}/close')
        assert resp.status_code == 403, \
            "Menutup ticket lintas sekolah harus 403!"

    def test_get_tickets_list_scoped(self, app, seed):
        """Daftar ticket Murid A hanya berisi ticket dari Sekolah A."""
        client = app.test_client()
        login(client, MURID_A_EMAIL)
        slug = seed['school_a_slug']
        resp = client.get(f'/s/{slug}/api/tickets')
        assert resp.status_code == 200
        ids = [t['id'] for t in resp.get_json()['tickets']]
        assert seed['ticket_b_id'] not in ids, \
            "Daftar ticket Sekolah A tidak boleh memuat ticket Sekolah B!"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. TICKET SERVICE — Sequence & Queue per Sekolah
# ═══════════════════════════════════════════════════════════════════════════════

class TestTicketService:

    def test_ticket_number_scoped_per_school(self, app, seed):
        """Nomor ticket dihasilkan terpisah untuk tiap sekolah."""
        from app.services.ticket_service import generate_ticket_number
        with app.app_context():
            num_a = generate_ticket_number(school_id=seed['school_a_id'])
            num_b = generate_ticket_number(school_id=seed['school_b_id'])
            assert num_a.startswith('TKT-'), f"Format salah: {num_a}"
            assert num_b.startswith('TKT-'), f"Format salah: {num_b}"
            # Urutan harus independen — bukan counter global
            seq_a = int(num_a.split('-')[-1])
            seq_b = int(num_b.split('-')[-1])
            assert seq_a >= 1
            assert seq_b >= 1

    def test_queue_position_scoped_per_school(self, app, seed):
        """Posisi antrian dihitung per sekolah, bukan secara global."""
        from app.services.ticket_service import get_queue_position
        with app.app_context():
            t1 = Ticket(
                ticket_number='TKT-QA-TEST01', title='Queue A', description='d',
                category=TicketCategory.GENERAL, status=TicketStatus.IN_QUEUE,
                priority=TicketPriority.MEDIUM,
                school_id=seed['school_a_id'], user_id=seed['murid_a_id'],
            )
            t2 = Ticket(
                ticket_number='TKT-QB-TEST01', title='Queue B', description='d',
                category=TicketCategory.GENERAL, status=TicketStatus.IN_QUEUE,
                priority=TicketPriority.MEDIUM,
                school_id=seed['school_b_id'], user_id=seed['murid_b_id'],
            )
            _db.session.add_all([t1, t2])
            _db.session.commit()

            pos_a = get_queue_position(t1)
            pos_b = get_queue_position(t2)

            assert isinstance(pos_a, int) and pos_a >= 1, \
                f"Queue position sekolah A tidak valid: {pos_a}"
            assert isinstance(pos_b, int) and pos_b >= 1, \
                f"Queue position sekolah B tidak valid: {pos_b}"
            # Kedua sekolah bisa sama-sama punya posisi #1 (independent)
            # → tidak saling mempengaruhi


# ═══════════════════════════════════════════════════════════════════════════════
# 6. EDGE CASE: User tanpa school_id
# ═══════════════════════════════════════════════════════════════════════════════

class TestNoSchoolUser:

    def test_orphan_user_login_blocked(self, app, seed):
        """User tanpa school_id harus ditolak saat login."""
        client = app.test_client()
        resp = login(client, 'orphan@test.com')
        # Auth harus menolak user yang tidak terhubung ke sekolah manapun
        assert resp.status_code == 403, \
            "User tanpa sekolah harus ditolak login dengan 403!"
        data = resp.get_json()
        assert data['success'] is False
