from __future__ import annotations

import copy
import json
import threading
import uuid
from datetime import date, datetime, timedelta
from json import JSONDecodeError
from pathlib import Path

from src.config.settings import (
    APP_DATA_PATH,
    COLLECTIONS,
    COMPANY_ADMIN,
    DEFAULT_STORAGE_MODE,
    FIREBASE_CREDENTIALS_PATH,
    GOOGLE_PROJECT_ID,
    GOOGLE_STORAGE_BUCKET,
    PLATFORM_ADMIN,
)
from src.models.billing_record import BillingRecord
from src.models.company import Company
from src.models.company_video import CompanyVideo
from src.models.employee import Employee
from src.models.platform_video import PlatformVideo
from src.models.user import User
from src.models.video_assignment import VideoAssignment
from src.utils.security import create_password_hash


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _date_iso(offset_days: int = 0) -> str:
    return (date.today() + timedelta(days=offset_days)).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def build_seed_dataset() -> dict:
    timestamp = _now_iso()

    company_alpha = Company(
        id="company-alpha",
        nome_fantasia="Alpha Florestal",
        razao_social="Alpha Florestal Seguranca Ltda",
        cnpj="12345678000190",
        nome_responsavel="Marina Almeida",
        telefone="47988110001",
        email="marina@alpha.com.br",
        endereco="Rua das Araucarias, 120",
        cidade="Lages",
        uf="SC",
        status_ativo=True,
        observacoes="Cliente piloto para trilha de videos diarios.",
        data_criacao=timestamp,
        data_atualizacao=timestamp,
    ).to_dict()
    company_beta = Company(
        id="company-beta",
        nome_fantasia="Beta Mineracao",
        razao_social="Beta Mineracao e Servicos S.A.",
        cnpj="98765432000155",
        nome_responsavel="Rafael Costa",
        telefone="31991112222",
        email="rafael@beta.com.br",
        endereco="Av. da Seguranca, 800",
        cidade="Belo Horizonte",
        uf="MG",
        status_ativo=True,
        observacoes="Base secundaria para isolamento multiempresa.",
        data_criacao=timestamp,
        data_atualizacao=timestamp,
    ).to_dict()

    employee_alpha_1 = Employee(
        id="employee-alpha-1",
        empresa_id="company-alpha",
        nome_completo="Carlos Silva",
        matricula="ALF-001",
        cpf_ou_identificador="12345678901",
        funcao="Operador de campo",
        email="carlos.silva@alpha.com.br",
        telefone="47999110011",
        login="carlos.silva",
        senha_hash=create_password_hash("Seg365@123"),
        status_ativo=True,
        data_admissao=_date_iso(-320),
        observacoes="Colaborador utilizado para homologacao do fluxo mobile.",
        data_criacao=timestamp,
        data_atualizacao=timestamp,
    ).to_dict()
    employee_alpha_2 = Employee(
        id="employee-alpha-2",
        empresa_id="company-alpha",
        nome_completo="Juliana Rocha",
        matricula="ALF-002",
        cpf_ou_identificador="10987654321",
        funcao="Tecnica de seguranca",
        email="juliana.rocha@alpha.com.br",
        telefone="47999110022",
        login="juliana.rocha",
        senha_hash=create_password_hash("Seg365@123"),
        status_ativo=True,
        data_admissao=_date_iso(-180),
        observacoes="Tecnica responsavel por reforcos comportamentais.",
        data_criacao=timestamp,
        data_atualizacao=timestamp,
    ).to_dict()
    employee_beta_1 = Employee(
        id="employee-beta-1",
        empresa_id="company-beta",
        nome_completo="Bruno Lima",
        matricula="BET-001",
        cpf_ou_identificador="55566677788",
        funcao="Mecanico",
        email="bruno.lima@beta.com.br",
        telefone="31992223344",
        login="bruno.lima",
        senha_hash=create_password_hash("Seg365@123"),
        status_ativo=True,
        data_admissao=_date_iso(-240),
        observacoes="Usado para validar isolamento entre empresas.",
        data_criacao=timestamp,
        data_atualizacao=timestamp,
    ).to_dict()

    users = [
        User(
            id="user-platform-1",
            username="plataforma.master",
            password_hash=create_password_hash("Seg365@123"),
            profile=PLATFORM_ADMIN,
            full_name="Administrador da Plataforma",
            status_ativo=True,
            created_at=timestamp,
            updated_at=timestamp,
        ).to_dict(),
        User(
            id="user-company-alpha",
            username="admin.videos",
            password_hash=create_password_hash("Video365@123"),
            profile=COMPANY_ADMIN,
            full_name="Administrador Global de Videos",
            status_ativo=True,
            created_at=timestamp,
            updated_at=timestamp,
        ).to_dict(),
        User(
            id="user-employee-alpha-1",
            username="carlos.silva",
            password_hash=employee_alpha_1["senha_hash"],
            profile="employee",
            full_name="Carlos Silva",
            company_id="company-alpha",
            employee_id="employee-alpha-1",
            status_ativo=True,
            created_at=timestamp,
            updated_at=timestamp,
        ).to_dict(),
        User(
            id="user-employee-alpha-2",
            username="juliana.rocha",
            password_hash=employee_alpha_2["senha_hash"],
            profile="employee",
            full_name="Juliana Rocha",
            company_id="company-alpha",
            employee_id="employee-alpha-2",
            status_ativo=True,
            created_at=timestamp,
            updated_at=timestamp,
        ).to_dict(),
        User(
            id="user-employee-beta-1",
            username="bruno.lima",
            password_hash=employee_beta_1["senha_hash"],
            profile="employee",
            full_name="Bruno Lima",
            company_id="company-beta",
            employee_id="employee-beta-1",
            status_ativo=True,
            created_at=timestamp,
            updated_at=timestamp,
        ).to_dict(),
    ]

    platform_videos = [
        PlatformVideo(
            id="platform-video-1",
            origem="platform",
            titulo="DDS: Uso correto de EPI",
            descricao="Video curto sobre uso e conferencia basica de EPI antes da atividade.",
            tema="EPI",
            categoria="Comportamental",
            url_video_ou_arquivo="https://www.youtube.com/watch?v=ysz5S6PUM-U",
            thumbnail="",
            duracao="04:15",
            status_publicado=True,
            data_disponibilizacao=_date_iso(-7),
            obrigatorio_por_padrao=True,
            criado_por="plataforma.master",
            data_criacao=timestamp,
            data_atualizacao=timestamp,
        ).to_dict(),
        PlatformVideo(
            id="platform-video-2",
            origem="platform",
            titulo="Bloqueio e etiquetagem",
            descricao="Procedimentos basicos para atividades com energia perigosa.",
            tema="LOTO",
            categoria="Procedimento",
            url_video_ou_arquivo="https://www.youtube.com/watch?v=jNQXAC9IVRw",
            thumbnail="",
            duracao="03:52",
            status_publicado=True,
            data_disponibilizacao=_date_iso(-4),
            obrigatorio_por_padrao=True,
            criado_por="plataforma.master",
            data_criacao=timestamp,
            data_atualizacao=timestamp,
        ).to_dict(),
        PlatformVideo(
            id="platform-video-3",
            origem="platform",
            titulo="Trabalho em altura: check rapido",
            descricao="Checklist minimo antes de subir para manutencao e acesso vertical.",
            tema="Altura",
            categoria="Checklist",
            url_video_ou_arquivo="https://www.youtube.com/watch?v=aqz-KE-bpKQ",
            thumbnail="",
            duracao="05:08",
            status_publicado=True,
            data_disponibilizacao=_date_iso(-1),
            obrigatorio_por_padrao=False,
            criado_por="plataforma.master",
            data_criacao=timestamp,
            data_atualizacao=timestamp,
        ).to_dict(),
    ]

    company_videos = [
        CompanyVideo(
            id="company-video-alpha-1",
            empresa_id="company-alpha",
            origem="company",
            titulo="Procedimento interno Alpha para area de campo",
            descricao="Orientacoes especificas da Alpha para entrada e saida de frente operacional.",
            tema="Procedimento interno",
            categoria="Operacional",
            url_video_ou_arquivo="https://www.youtube.com/watch?v=ScMzIvxBSi4",
            thumbnail="",
            duracao="06:10",
            status_publicado=True,
            data_disponibilizacao=_date_iso(-2),
            obrigatorio_por_padrao=True,
            criado_por="admin.alfa",
            data_criacao=timestamp,
            data_atualizacao=timestamp,
        ).to_dict(),
        CompanyVideo(
            id="company-video-beta-1",
            empresa_id="company-beta",
            origem="company",
            titulo="Pontos criticos da oficina Beta",
            descricao="Recado diario sobre ordem, limpeza e liberacao de manutencao.",
            tema="Oficina",
            categoria="Rotina",
            url_video_ou_arquivo="https://www.youtube.com/watch?v=HluANRwPyNo",
            thumbnail="",
            duracao="04:40",
            status_publicado=True,
            data_disponibilizacao=_date_iso(-2),
            obrigatorio_por_padrao=True,
            criado_por="admin.beta",
            data_criacao=timestamp,
            data_atualizacao=timestamp,
        ).to_dict(),
    ]

    video_assignments = [
        VideoAssignment(
            id="assignment-alpha-today-1",
            empresa_id="company-alpha",
            funcionario_id="employee-alpha-1",
            video_id="platform-video-1",
            origem_video="platform",
            data_referencia=_date_iso(),
            status="pending",
            data_visualizacao="",
            confirmado_manual=False,
            percentual_visualizado_future=None,
            criado_em=timestamp,
            atualizado_em=timestamp,
        ).to_dict(),
        VideoAssignment(
            id="assignment-alpha-pending-2",
            empresa_id="company-alpha",
            funcionario_id="employee-alpha-1",
            video_id="company-video-alpha-1",
            origem_video="company",
            data_referencia=_date_iso(-1),
            status="pending",
            data_visualizacao="",
            confirmado_manual=False,
            percentual_visualizado_future=None,
            criado_em=timestamp,
            atualizado_em=timestamp,
        ).to_dict(),
        VideoAssignment(
            id="assignment-alpha-completed-3",
            empresa_id="company-alpha",
            funcionario_id="employee-alpha-1",
            video_id="platform-video-2",
            origem_video="platform",
            data_referencia=_date_iso(-2),
            status="completed",
            data_visualizacao=timestamp,
            confirmado_manual=True,
            percentual_visualizado_future=None,
            criado_em=timestamp,
            atualizado_em=timestamp,
        ).to_dict(),
        VideoAssignment(
            id="assignment-alpha-juliana-1",
            empresa_id="company-alpha",
            funcionario_id="employee-alpha-2",
            video_id="platform-video-3",
            origem_video="platform",
            data_referencia=_date_iso(),
            status="pending",
            data_visualizacao="",
            confirmado_manual=False,
            percentual_visualizado_future=None,
            criado_em=timestamp,
            atualizado_em=timestamp,
        ).to_dict(),
        VideoAssignment(
            id="assignment-beta-1",
            empresa_id="company-beta",
            funcionario_id="employee-beta-1",
            video_id="company-video-beta-1",
            origem_video="company",
            data_referencia=_date_iso(),
            status="pending",
            data_visualizacao="",
            confirmado_manual=False,
            percentual_visualizado_future=None,
            criado_em=timestamp,
            atualizado_em=timestamp,
        ).to_dict(),
    ]

    billing_records = [
        BillingRecord(
            id="billing-alpha-1",
            empresa_id="company-alpha",
            descricao="Plano demo mensal - abril",
            valor=1490.0,
            status="pending",
            data_geracao=_date_iso(-5),
            data_pagamento="",
            observacoes="Modulo demonstrativo sem integracao real.",
        ).to_dict(),
        BillingRecord(
            id="billing-alpha-2",
            empresa_id="company-alpha",
            descricao="Horas adicionais de onboarding",
            valor=390.0,
            status="paid",
            data_geracao=_date_iso(-25),
            data_pagamento=_date_iso(-18),
            observacoes="Historico de exemplo para a area financeira demo.",
        ).to_dict(),
        BillingRecord(
            id="billing-beta-1",
            empresa_id="company-beta",
            descricao="Plano demo mensal - abril",
            valor=990.0,
            status="pending",
            data_geracao=_date_iso(-4),
            data_pagamento="",
            observacoes="Registro mantido para validacao de isolamento por empresa.",
        ).to_dict(),
    ]

    return {
        "users": users,
        "companies": [company_alpha, company_beta],
        "employees": [employee_alpha_1, employee_alpha_2, employee_beta_1],
        "platform_videos": platform_videos,
        "company_videos": company_videos,
        "video_assignments": video_assignments,
        "billing_records": billing_records,
        "safety_images": [],
        "image_assignments": [],
        "meta": {
            "storage_mode": DEFAULT_STORAGE_MODE,
            "google_project_id": GOOGLE_PROJECT_ID,
            "google_storage_bucket": GOOGLE_STORAGE_BUCKET,
            "last_seed_at": timestamp,
        },
    }


class AbstractStorageProvider:
    def read(self) -> dict:
        raise NotImplementedError

    def write(self, data: dict) -> None:
        raise NotImplementedError


class LocalJsonStorageProvider(AbstractStorageProvider):
    def __init__(self, data_path: Path) -> None:
        self.data_path = data_path
        self._lock = threading.Lock()

    def _ensure_file(self) -> None:
        with self._lock:
            if self.data_path.exists() and self.data_path.stat().st_size > 0:
                return
            _ensure_parent(self.data_path)
            temp_path = self.data_path.with_suffix(".tmp")
            with temp_path.open("w", encoding="utf-8") as handle:
                json.dump(build_seed_dataset(), handle, ensure_ascii=False, indent=2)
            temp_path.replace(self.data_path)

    def read(self) -> dict:
        self._ensure_file()
        with self._lock:
            try:
                with self.data_path.open("r", encoding="utf-8") as handle:
                    data = json.load(handle)
            except (JSONDecodeError, OSError):
                data = build_seed_dataset()
                temp_path = self.data_path.with_suffix(".tmp")
                with temp_path.open("w", encoding="utf-8") as handle:
                    json.dump(data, handle, ensure_ascii=False, indent=2)
                temp_path.replace(self.data_path)
        for collection in COLLECTIONS:
            data.setdefault(collection, [])
        data.setdefault("meta", {})
        return data

    def write(self, data: dict) -> None:
        self._ensure_file()
        with self._lock:
            temp_path = self.data_path.with_suffix(".tmp")
            with temp_path.open("w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
            temp_path.replace(self.data_path)


class FirestoreStorageProvider(AbstractStorageProvider):
    def __init__(self) -> None:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if not firebase_admin._apps:
            options = {
                "projectId": GOOGLE_PROJECT_ID or None,
                "storageBucket": GOOGLE_STORAGE_BUCKET or None,
            }
            if FIREBASE_CREDENTIALS_PATH:
                credential = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(credential, options)
            else:
                firebase_admin.initialize_app(options=options)
        self.db = firestore.client()

    def read(self) -> dict:
        data = {collection: [] for collection in COLLECTIONS}
        for collection in COLLECTIONS:
            for document in self.db.collection(collection).stream():
                payload = document.to_dict() or {}
                payload.setdefault("id", document.id)
                data[collection].append(payload)
        data["meta"] = {
            "storage_mode": "firestore",
            "google_project_id": GOOGLE_PROJECT_ID,
            "google_storage_bucket": GOOGLE_STORAGE_BUCKET,
        }
        return data

    def write(self, data: dict) -> None:
        for collection in COLLECTIONS:
            collection_ref = self.db.collection(collection)
            current_docs = {document.id for document in collection_ref.stream()}
            incoming_docs = {record["id"] for record in data.get(collection, []) if record.get("id")}

            batch = self.db.batch()
            for record in data.get(collection, []):
                record_id = str(record["id"])
                batch.set(collection_ref.document(record_id), record)
            for stale_id in current_docs - incoming_docs:
                batch.delete(collection_ref.document(stale_id))
            batch.commit()


class StorageService:
    def __init__(self, provider: AbstractStorageProvider) -> None:
        self.provider = provider
        self._write_lock = threading.Lock()

    def load(self) -> dict:
        data = copy.deepcopy(self.provider.read())
        try:
            from src.services.local_video_service import sync_local_folder_videos

            data, changed = sync_local_folder_videos(data)
            if changed:
                self.provider.write(copy.deepcopy(data))
        except Exception:
            pass
        return data

    def save(self, payload: dict) -> None:
        with self._write_lock:
            self.provider.write(copy.deepcopy(payload))

    def list_records(self, collection: str) -> list[dict]:
        return self.load().get(collection, [])

    def get_record(self, collection: str, record_id: str) -> dict | None:
        return next((record for record in self.list_records(collection) if str(record.get("id")) == str(record_id)), None)

    def upsert_record(self, collection: str, record: dict, record_id: str | None = None) -> dict:
        data = self.load()
        records = data.setdefault(collection, [])
        resolved_id = record_id or record.get("id") or _new_id(collection.rstrip("s"))
        record["id"] = resolved_id

        updated = False
        for index, current in enumerate(records):
            if str(current.get("id")) == str(resolved_id):
                records[index] = record
                updated = True
                break
        if not updated:
            records.append(record)
        self.save(data)
        return record

    def delete_record(self, collection: str, record_id: str) -> None:
        data = self.load()
        data[collection] = [record for record in data.get(collection, []) if str(record.get("id")) != str(record_id)]
        self.save(data)


_storage_service: StorageService | None = None


def get_storage_service() -> StorageService:
    global _storage_service
    if _storage_service is not None:
        return _storage_service

    if DEFAULT_STORAGE_MODE == "firestore":
        try:
            provider = FirestoreStorageProvider()
        except Exception:
            provider = LocalJsonStorageProvider(APP_DATA_PATH)
    else:
        provider = LocalJsonStorageProvider(APP_DATA_PATH)

    _storage_service = StorageService(provider)
    return _storage_service
