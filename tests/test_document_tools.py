"""Tests for document tools (mocked — no real CATIA)."""

from unittest.mock import MagicMock
import pytest


@pytest.fixture(autouse=True)
def fresh_com_mocks():
    import sys
    from conftest import _install_com_mocks
    _install_com_mocks()
    yield


@pytest.fixture
def conn_mock():
    mock = MagicMock()
    mock.is_connected = True
    mock.active_document = MagicMock()
    mock.active_document.Name = "Test.Part"
    mock.active_document.FullName = "C:/Test.Part"
    mock.documents = MagicMock()
    mock.documents.Count = 0
    mock.documents.Add.return_value = MagicMock()
    mock.documents.Add.return_value.Part.Name = "Part.1"
    mock.documents.Add.return_value.Product.Name = "Product.1"
    mock.documents.Open.return_value = MagicMock()
    mock.documents.Open.return_value.Name = "Opened.Part"
    mock.documents.Item.return_value = MagicMock()
    mock.documents.Item.return_value.Name = "Part.1"
    mock.documents.Item.return_value.FullName = "C:/Part.1"
    mock.documents.Item.return_value.Part.Name = "Part.1"
    mock.documents.Item.return_value.Product = MagicMock(side_effect=Exception("no product"))
    mock.refresh_display = MagicMock()
    mock.normalize_path.return_value = "C:/out/part.stp"
    return mock


@pytest.fixture
def doc_tools(conn_mock):
    from catia_mcp.tools.document import DocumentTools
    return DocumentTools(conn_mock)


# ── FR-04.1 catia_new_part ──────────────────────────────────────────────

class TestNewPart:
    def test_new_part_default(self, doc_tools, conn_mock):
        result = doc_tools.execute("catia_new_part", {})
        assert isinstance(result, str)
        assert "Part" in result
        assert "created" in result.lower() or "Part" in result
        conn_mock.documents.Add.assert_called_with("Part")

    def test_new_part_with_name(self, doc_tools, conn_mock):
        conn_mock.documents.Add.return_value.Part.Name = "MyPart"
        result = doc_tools.execute("catia_new_part", {"name": "MyPart"})
        assert "MyPart" in result
        conn_mock.documents.Add.assert_called_with("Part")

    def test_new_part_calls_docs_add(self, doc_tools, conn_mock):
        doc_tools.execute("catia_new_part", {})
        conn_mock.documents.Add.assert_called_once()
        conn_mock.refresh_display.assert_called()


# ── FR-04.2 catia_new_product ───────────────────────────────────────────

class TestNewProduct:
    def test_new_product_default(self, doc_tools, conn_mock):
        result = doc_tools.execute("catia_new_product", {})
        assert isinstance(result, str)
        assert "Product" in result or "product" in result.lower()
        conn_mock.documents.Add.assert_called_with("Product")

    def test_new_product_with_name(self, doc_tools, conn_mock):
        conn_mock.documents.Add.return_value.Product.Name = "MyProduct"
        result = doc_tools.execute("catia_new_product", {"name": "MyProduct"})
        assert "MyProduct" in result

    def test_new_product_calls_docs_add(self, doc_tools, conn_mock):
        doc_tools.execute("catia_new_product", {})
        conn_mock.documents.Add.assert_called_once()
        conn_mock.refresh_display.assert_called()


# ── FR-04.3 catia_open_document ─────────────────────────────────────────

class TestOpenDocument:
    def test_open_document_valid(self, doc_tools, conn_mock):
        result = doc_tools.execute("catia_open_document", {"file_path": "C:/test.Part"})
        assert isinstance(result, str)
        assert "Opened.Part" in result or "opened" in result.lower()

    def test_open_document_calls_docs_open(self, doc_tools, conn_mock):
        doc_tools.execute("catia_open_document", {"file_path": "C:/test.Part"})
        conn_mock.documents.Open.assert_called()

    def test_open_document_empty_path_raises(self, doc_tools):
        with pytest.raises(ValueError, match="must not be empty"):
            doc_tools.execute("catia_open_document", {"file_path": ""})

    def test_open_document_relative_path_raises(self, doc_tools):
        with pytest.raises(ValueError, match="does not appear to be a valid"):
            doc_tools.execute("catia_open_document", {"file_path": "relative.part"})

    def test_open_document_non_string_raises(self, doc_tools):
        with pytest.raises(ValueError, match="must be a string"):
            doc_tools.execute("catia_open_document", {"file_path": 123})


# ── FR-04.4 catia_save_document ─────────────────────────────────────────

class TestSaveDocument:
    def test_save_document_no_path(self, doc_tools, conn_mock):
        result = doc_tools.execute("catia_save_document", {})
        assert isinstance(result, str)
        assert "saved" in result.lower()
        conn_mock.active_document.Save.assert_called()

    def test_save_document_with_path(self, doc_tools, conn_mock):
        result = doc_tools.execute("catia_save_document", {"file_path": "C:/out/test.Part"})
        assert isinstance(result, str)
        assert "saved" in result.lower()
        conn_mock.active_document.SaveAs.assert_called()

    def test_save_document_relative_path_raises(self, doc_tools):
        with pytest.raises(ValueError, match="does not appear to be a valid"):
            doc_tools.execute("catia_save_document", {"file_path": "relative.part"})


# ── FR-04.5 catia_close_document ────────────────────────────────────────

class TestCloseDocument:
    def test_close_document_no_save(self, doc_tools, conn_mock):
        result = doc_tools.execute("catia_close_document", {"save": False})
        assert isinstance(result, str)
        assert "closed" in result.lower()
        conn_mock.active_document.Close.assert_called()

    def test_close_document_with_save(self, doc_tools, conn_mock):
        result = doc_tools.execute("catia_close_document", {"save": True})
        assert isinstance(result, str)
        assert "closed" in result.lower()
        assert "saved" in result.lower()
        conn_mock.active_document.Save.assert_called()
        conn_mock.active_document.Close.assert_called()


# ── FR-04.6 catia_list_documents ────────────────────────────────────────

class TestListDocuments:
    def test_list_documents_empty(self, doc_tools, conn_mock):
        conn_mock.documents.Count = 0
        result = doc_tools.execute("catia_list_documents", {})
        assert "No documents" in result or "open" in result.lower()

    def test_list_documents_with_docs(self, doc_tools, conn_mock):
        conn_mock.documents.Count = 2
        doc1 = MagicMock()
        doc1.Name = "Part.1"
        doc1.FullName = "C:/Part.1"
        doc1.Part.Name = "Part.1"
        doc1.Product = MagicMock(side_effect=Exception("no product"))

        doc2 = MagicMock()
        doc2.Name = "Product.1"
        doc2.FullName = "C:/Product.1"
        doc2.Part = MagicMock(side_effect=Exception("no part"))
        doc2.Product.Name = "Product.1"

        conn_mock.documents.Item.side_effect = lambda i: [doc1, doc2][i - 1]
        result = doc_tools.execute("catia_list_documents", {})
        assert isinstance(result, str)
        assert "Part.1" in result

    def test_list_documents_part_type(self, doc_tools, conn_mock):
        conn_mock.documents.Count = 1
        result = doc_tools.execute("catia_list_documents", {})
        assert "CATPart" in result or "Part" in result


# ── FR-04.7 catia_get_active_document_info ──────────────────────────────

class TestGetActiveDocumentInfo:
    def test_get_info_part(self, doc_tools, conn_mock):
        doc = conn_mock.active_document
        part = MagicMock()
        part.Name = "TestPart"
        bodies = MagicMock()
        bodies.Count = 1
        body = MagicMock()
        body.Name = "PartBody"
        body.Shapes.Count = 0
        bodies.Item.return_value = body
        part.Bodies = bodies
        part.HybridBodies.Count = 0
        part.Parameters.Count = 0
        doc.Part = part
        doc.Product = MagicMock(side_effect=Exception("no product"))

        result = doc_tools.execute("catia_get_active_document_info", {})
        assert isinstance(result, str)
        assert "CATPart" in result

    def test_get_info_product(self, doc_tools, conn_mock):
        doc = conn_mock.active_document
        doc.Part = None
        type(doc).Part = property(lambda self: (_ for _ in ()).throw(Exception("no part")))
        product = MagicMock()
        product.Name = "TestProduct"
        product.PartNumber = "PROD.001"
        prods = MagicMock()
        prods.Count = 0
        product.Products = prods
        doc.Product = product

        result = doc_tools.execute("catia_get_active_document_info", {})
        assert isinstance(result, str)
        assert "CATProduct" in result

    def test_get_info_unknown(self, doc_tools, conn_mock):
        doc = conn_mock.active_document
        doc.Part = None
        type(doc).Part = property(lambda self: (_ for _ in ()).throw(Exception("no part")))
        doc.Product = None
        type(doc).Product = property(lambda self: (_ for _ in ()).throw(Exception("no product")))

        result = doc_tools.execute("catia_get_active_document_info", {})
        assert isinstance(result, str)
        assert "Unknown" in result


# ── Existing tests (validation & routing) ────────────────────────────────

class TestOpenDocumentValidation:
    def test_empty_path_raises(self, doc_tools):
        with pytest.raises(ValueError, match="must not be empty"):
            doc_tools._open_document("")

    def test_relative_path_raises(self, doc_tools):
        with pytest.raises(ValueError, match="does not appear to be a valid"):
            doc_tools._open_document("relative.part")

    def test_non_string_raises(self, doc_tools):
        with pytest.raises(ValueError, match="must be a string"):
            doc_tools._open_document(123)


class TestSaveDocumentValidation:
    def test_save_no_path(self, doc_tools):
        result = doc_tools._save_document(None)
        assert "saved" in result.lower()

    def test_save_relative_path_raises(self, doc_tools):
        with pytest.raises(ValueError, match="does not appear to be a valid"):
            doc_tools._save_document("relative.part")


class TestExecuteRouting:
    def test_catia_close_routes(self, doc_tools, conn_mock):
        conn_mock.close.return_value = "CATIA V5 has been closed"
        result = doc_tools.execute("catia_close", {})
        assert "closed" in result.lower()
        conn_mock.close.assert_called_once()

    def test_catia_connect_routes(self, doc_tools, conn_mock):
        conn_mock.connect.return_value = "Connected to running CATIA V5"
        result = doc_tools.execute("catia_connect", {})
        assert "Connected" in result
        conn_mock.connect.assert_called_once()

    def test_catia_disconnect_routes(self, doc_tools, conn_mock):
        conn_mock.disconnect.return_value = "Disconnected from CATIA V5"
        result = doc_tools.execute("catia_disconnect", {})
        assert "Disconnected" in result

    def test_unknown_tool_raises(self, doc_tools):
        with pytest.raises(ValueError, match="Unknown document tool"):
            doc_tools.execute("catia_nonexistent", {})


class TestToolDefinitions:
    def test_catia_close_present(self, doc_tools):
        defs = doc_tools.get_tool_definitions()
        names = [d["name"] for d in defs]
        assert "catia_close" in names

    def test_all_10_tools_present(self, doc_tools):
        defs = doc_tools.get_tool_definitions()
        assert len(defs) == 10
