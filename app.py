# Sistema funcional em Python com Streamlit para monitoramento de performance da equipe de vendas da MARMORIZE

import streamlit as st
import pandas as pd
import datetime
import sqlite3

st.set_page_config(page_title="Monitoramento MARMORIZE", layout="wide")

st.title("📊 Sistema de Monitoramento de Vendas - MARMORIZE")

# --- Banco de Dados SQLite ---
conn = sqlite3.connect("marmorize.db", check_same_thread=False)
c = conn.cursor()

# Tabelas de Funcionários e Vendas
c.execute("""
CREATE TABLE IF NOT EXISTS funcionarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL,
    data_admissao TEXT NOT NULL
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    mes TEXT,
    rochas REAL,
    decorativos REAL,
    itens REAL,
    total REAL,
    caminho TEXT,
    comissao REAL,
    bonus_fidelidade REAL,
    bonus_forja REAL
)
""")
conn.commit()

# --- Cadastro de Funcionário ---
st.sidebar.header("Cadastrar Funcionário")
with st.sidebar.form("cadastro_form"):
    nome = st.text_input("Nome do funcionário")
    data_admissao = st.date_input("Data de admissão", value=datetime.date.today())
    cadastrar = st.form_submit_button("Cadastrar")
    if cadastrar and nome:
        try:
            c.execute("INSERT INTO funcionarios (nome, data_admissao) VALUES (?, ?)", (nome, data_admissao.isoformat()))
            conn.commit()
            st.success(f"Funcionário {nome} cadastrado com sucesso!")
        except sqlite3.IntegrityError:
            st.warning("Funcionário já está cadastrado.")

# --- Registro de Vendas ---
st.sidebar.header("Registrar Vendas")
c.execute("SELECT nome FROM funcionarios")
vendedores = [row[0] for row in c.fetchall()]

if vendedores:
    with st.sidebar.form("vendas_form"):
        vendedor = st.selectbox("Funcionário", vendedores)
        mes = st.selectbox("Mês de Referência", ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"])
        rochas = st.number_input("Valor de Rochas (R$)", min_value=0.0, step=100.0)
        decorativos = st.number_input("Valor de Decorativos (R$)", min_value=0.0, step=100.0)
        itens = st.number_input("Valor de Itens de Missão (R$)", min_value=0.0, step=100.0)
        enviar = st.form_submit_button("Registrar Venda")

        if enviar:
            total = rochas + decorativos + itens
            if itens >= 3500:
                caminho = "C"
                comissao = rochas * 0.0375 + decorativos * 0.045
            elif itens >= 2500:
                caminho = "B"
                comissao = rochas * 0.025 + decorativos * 0.025
            elif itens >= 1500:
                caminho = "A"
                comissao = rochas * 0.02 + decorativos * 0.015
            else:
                caminho = "-"
                comissao = 0.0

            bonus_forja = (itens // 1500) * 50 if caminho == "C" else 0

            # Buscar data de admissão
            c.execute("SELECT data_admissao FROM funcionarios WHERE nome = ?", (vendedor,))
            data_adm_str = c.fetchone()[0]
            data_adm = datetime.datetime.fromisoformat(data_adm_str).date()
            anos_empresa = (datetime.date.today() - data_adm).days // 365
            bonus_fidelidade = anos_empresa * 0.001 * (rochas + decorativos) if caminho != "-" else 0

            c.execute("""
                INSERT INTO vendas (nome, mes, rochas, decorativos, itens, total, caminho, comissao, bonus_fidelidade, bonus_forja)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (vendedor, mes, rochas, decorativos, itens, total, caminho, comissao, bonus_fidelidade, bonus_forja))
            conn.commit()
            st.success("Venda registrada com sucesso!")
else:
    st.sidebar.info("Cadastre ao menos um funcionário para registrar vendas.")

# --- Dashboard ---
st.subheader("📈 Dashboard de Performance")
df_vendas = pd.read_sql_query("SELECT * FROM vendas", conn)

if df_vendas.empty:
    st.info("Nenhuma venda registrada ainda.")
else:
    filtro_mes = st.selectbox("Filtrar por mês", ["Todos"] + sorted(df_vendas["mes"].unique()))
    if filtro_mes != "Todos":
        df_filtrado = df_vendas[df_vendas["mes"] == filtro_mes]
    else:
        df_filtrado = df_vendas.copy()

    total_geral = df_filtrado.groupby(["nome", "caminho"])[["total", "comissao", "bonus_fidelidade", "bonus_forja"]].sum().reset_index().sort_values(by="total", ascending=False)
    st.dataframe(total_geral, use_container_width=True)
    st.bar_chart(total_geral.set_index("nome")["total"])

    st.subheader("📄 Relatório Completo")
    st.dataframe(df_filtrado, use_container_width=True)
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Baixar Relatório (CSV)", data=csv, file_name="relatorio_marmorize.csv", mime="text/csv")

    st.subheader("🔍 Visualização Individual")
    nome_selecionado = st.selectbox("Selecione um funcionário", sorted(df_filtrado["nome"].unique()))
    df_individual = df_filtrado[df_filtrado["nome"] == nome_selecionado]
    st.dataframe(df_individual, use_container_width=True)
    total_ind = df_individual[["total", "comissao", "bonus_fidelidade", "bonus_forja"]].sum()
    st.metric("Total Vendido", f"R$ {total_ind['total']:.2f}")
    st.metric("Comissão", f"R$ {total_ind['comissao']:.2f}")
    st.metric("Fidelidade Premiada", f"R$ {total_ind['bonus_fidelidade']:.2f}")
    st.metric("Forja Suprema (VR)", f"R$ {total_ind['bonus_forja']:.2f}")
