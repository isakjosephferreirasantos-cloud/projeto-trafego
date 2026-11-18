import unittest

from app import app as default_app
from app import create_app
from extensions import db
from models import Cargo, User


class TestConfig:
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    WTF_CSRF_ENABLED = False


class PublicSiteIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    @classmethod
    def tearDownClass(cls):
        with default_app.app_context():
            db.session.remove()
            db.engine.dispose()

    def register_user(self, email="operador@example.test"):
        return self.client.post(
            "/auth/registro?next=/",
            data={
                "nome": "Operador Teste",
                "email": email,
                "senha": "Senha-teste-123",
                "confirmar_senha": "Senha-teste-123",
            },
        )

    def test_unregistered_visitors_are_redirected_to_registration(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/auth/registro?next=/")
        self.assertEqual(self.client.get("/api/posts").status_code, 302)
        self.assertEqual(self.client.get("/assets/simulador3d.js").status_code, 302)

    def test_registration_unlocks_public_home(self):
        registration = self.register_user()
        self.assertEqual(registration.status_code, 302)
        self.assertEqual(registration.headers["Location"], "/")

        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("<h1>Fluxo <span>ST</span></h1>", response.get_data(as_text=True))
        self.assertIn('id="city-map"', response.get_data(as_text=True))
        self.assertNotIn("__STUDY_POINTS_JSON__", response.get_data(as_text=True))
        self.assertIn('<a href="/" class="site-link">Acessar conta</a>', response.get_data(as_text=True))
        self.assertIn('href="/admin"', response.get_data(as_text=True))
        self.assertIn('location.replace("/admin")', response.get_data(as_text=True))
        self.assertNotIn("startPresenceHeartbeat();", response.get_data(as_text=True))
        self.assertNotIn("expira após 5 minutos sem atividade", response.get_data(as_text=True))

    def test_management_link_enters_flask_auth_flow(self):
        response = self.client.get("/admin")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login?next=/painel", response.headers["Location"])
        self.assertEqual(self.client.get("/painel").status_code, 302)

    def test_admin_can_publish_and_remove_site_updates(self):
        with self.app.app_context():
            usuario = User(
                nome="Admin Teste",
                email="admin@example.test",
                cargo=Cargo.ADMINISTRADOR,
                ativo=True,
            )
            usuario.definir_senha("Senha-teste-123")
            db.session.add(usuario)
            db.session.commit()

        login = self.client.post(
            "/auth/login",
            data={"email": "admin@example.test", "senha": "Senha-teste-123"},
        )
        self.assertEqual(login.status_code, 302)
        management_page = self.client.get("/publicacoes/")
        self.assertEqual(management_page.status_code, 200)
        self.assertIn("Compartilhe uma novidade", management_page.get_data(as_text=True))
        published = self.client.post(
            "/publicacoes/",
            data={"titulo": "Obras de mobilidade", "texto": "Acompanhe as próximas etapas."},
        )
        self.assertEqual(published.status_code, 302)
        posts = self.client.get("/api/posts").json["posts"]
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]["title"], "Obras de mobilidade")
        self.assertEqual(posts[0]["body"], "Acompanhe as próximas etapas.")

        removed = self.client.post(f"/publicacoes/{posts[0]['id']}/excluir")
        self.assertEqual(removed.status_code, 302)
        self.assertEqual(self.client.get("/api/posts").json, {"posts": []})

    def test_login_opens_panel_and_panel_links_back_to_public_site(self):
        with self.app.app_context():
            usuario = User(
                nome="Admin Teste",
                email="admin@example.test",
                cargo=Cargo.ADMINISTRADOR,
                ativo=True,
            )
            usuario.definir_senha("Senha-teste-123")
            db.session.add(usuario)
            db.session.commit()

        login_page = self.client.get("/auth/login")
        self.assertEqual(login_page.status_code, 200)
        self.assertIn('<h1>Fluxo <span class="text-green">ST</span></h1>', login_page.get_data(as_text=True))

        login = self.client.post(
            "/auth/login",
            data={"email": "admin@example.test", "senha": "Senha-teste-123"},
        )
        self.assertEqual(login.status_code, 302)
        self.assertEqual(login.headers["Location"], "/painel")
        dashboard = self.client.get("/painel")
        self.assertEqual(dashboard.status_code, 200)
        dashboard_html = dashboard.get_data(as_text=True)
        self.assertIn("Site público", dashboard_html)
        self.assertIn("<h1>Admin Teste</h1>", dashboard_html)
        self.assertIn('href="/usuarios/"', dashboard_html)
        users_page = self.client.get("/usuarios/")
        self.assertEqual(users_page.status_code, 200)
        self.assertIn("Pessoas cadastradas", users_page.get_data(as_text=True))
        self.assertIn("Admin Teste", users_page.get_data(as_text=True))

    def test_public_site_dependencies_are_served(self):
        self.register_user()
        self.assertEqual(self.client.get("/publicacoes/").status_code, 403)
        self.assertEqual(self.client.get("/usuarios/").status_code, 403)
        dashboard = self.client.get("/painel")
        self.assertEqual(dashboard.status_code, 200)
        self.assertNotIn('href="/usuarios/"', dashboard.get_data(as_text=True))
        response = self.client.get("/assets/simulador3d.js")
        self.assertEqual(response.status_code, 200)
        response.close()
        self.assertEqual(self.client.get("/api/posts").json, {"posts": []})


if __name__ == "__main__":
    unittest.main()
