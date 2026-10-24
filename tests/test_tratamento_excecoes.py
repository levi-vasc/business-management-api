import asyncio
import json
import unittest
import uuid
from app.main import app


class TestTratamentoExcecoes(unittest.TestCase):
    def _executar_requisicao(self, method: str, path: str, body: dict = None, headers: list = None):
        """Helper para executar requisições ASGI contra o app e retornar (status_code, json_payload)."""
        body_bytes = json.dumps(body).encode("utf-8") if body is not None else b""
        req_headers = [(b"host", b"testserver")]
        if body is not None:
            req_headers.append((b"content-type", b"application/json"))
        if headers:
            req_headers.extend(headers)

        response_body = []
        status_code = [None]

        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": method,
            "path": path,
            "raw_path": path.encode("utf-8"),
            "query_string": b"",
            "headers": req_headers,
        }

        async def receive():
            return {"type": "http.request", "body": body_bytes, "more_body": False}

        async def send(message):
            if message["type"] == "http.response.start":
                status_code[0] = message["status"]
            elif message["type"] == "http.response.body":
                response_body.append(message.get("body", b""))

        asyncio.run(app(scope, receive, send))

        raw_content = b"".join(response_body).decode("utf-8")
        try:
            payload = json.loads(raw_content)
        except Exception:
            payload = raw_content

        return status_code[0], payload

    def test_404_rota_inexistente(self):
        """Garante que rotas inexistentes retornam 404 com o modelo padronizado e nunca 200"""
        status, payload = self._executar_requisicao("GET", "/endpoint-que-nao-existe")
        self.assertEqual(status, 404)
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["status_code"], 404)
        self.assertEqual(payload["error"], "Not Found")
        self.assertIn("message", payload)
        self.assertEqual(payload["path"], "/endpoint-que-nao-existe")
        self.assertIn("timestamp", payload)

    def test_400_dados_invalidos_validacao(self):
        """Garante que requisição com dados faltantes/inválidos retorna 400 com campos no detalhe"""
        status, payload = self._executar_requisicao("POST", "/produtos/", body={})
        self.assertEqual(status, 400)
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["status_code"], 400)
        self.assertEqual(payload["error"], "Bad Request")
        self.assertIn("Dados fornecidos na requisição são inválidos", payload["message"])
        self.assertIsInstance(payload["detalhes"], list)
        self.assertTrue(len(payload["detalhes"]) > 0)
        campos_com_erro = [d["campo"] for d in payload["detalhes"]]
        self.assertIn("nome", campos_com_erro)
        self.assertIn("codigo", campos_com_erro)

    def test_400_regra_de_negocio(self):
        """Garante que violações de negócio (ex: tipo de movimentação inválido) retornam 400 padronizado"""
        status, payload = self._executar_requisicao(
            "POST",
            "/movimentacoes/",
            body={
                "produto_id": str(uuid.uuid4()),
                "tipo": "TRANSFERENCIA_INVALIDA",
                "qnt": 5,
            },
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["status_code"], 400)
        self.assertEqual(payload["error"], "Bad Request")
        self.assertIn("Tipo de movimentação inválido", payload["message"])
        self.assertEqual(payload["path"], "/movimentacoes/")

    def test_404_recurso_nao_encontrado(self):
        """Garante que busca por ID inexistente retorna 404 padronizado"""
        id_aleatorio = str(uuid.uuid4())
        status, payload = self._executar_requisicao("GET", f"/produtos/{id_aleatorio}")
        self.assertEqual(status, 404)
        self.assertEqual(payload["status_code"], 404)
        self.assertEqual(payload["error"], "Not Found")
        self.assertEqual(payload["message"], "Produto não encontrado.")
        self.assertEqual(payload["path"], f"/produtos/{id_aleatorio}")

    def test_500_sem_stack_trace_exposto(self):
        """Garante que falhas internas não exponham stack traces ao cliente e retornem 500"""
        @app.get("/rota-teste-erro-interno")
        def rota_com_falha():
            raise ZeroDivisionError("Erro critico interno simulado para teste")

        status, payload = self._executar_requisicao("GET", "/rota-teste-erro-interno")
        self.assertEqual(status, 500)
        self.assertEqual(payload["status_code"], 500)
        self.assertEqual(payload["error"], "Internal Server Error")
        self.assertEqual(
            payload["message"],
            "Ocorreu um erro interno inesperado no servidor. Nossa equipe foi notificada.",
        )
        self.assertIsNone(payload["detalhes"])
        # Garante que nenhuma menção a Traceback, ZeroDivisionError ou arquivos Python vazou no JSON
        payload_str = json.dumps(payload)
        self.assertNotIn("Traceback", payload_str)
        self.assertNotIn("ZeroDivisionError", payload_str)
        self.assertNotIn(".py", payload_str)


if __name__ == "__main__":
    unittest.main()
