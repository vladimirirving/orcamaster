from app.models import Base, Empresa, Usuario, Obra, Versao, Grupo
from app.models import Composicao, Insumo, Item, BDI, CronogramaLinha, Medicao, PacoteJob


def test_all_models_import():
    tables = Base.metadata.tables
    expected = {
        "empresa", "usuario", "obra", "versao", "grupo",
        "composicao", "insumo", "item", "bdi",
        "cronograma_linha", "medicao", "pacote_job",
    }
    assert expected.issubset(set(tables.keys()))
