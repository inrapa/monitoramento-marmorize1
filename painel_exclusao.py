# Painel de Exclusão (Acesso restrito)

import streamlit as st
import sqlite3
import pandas as pd
import datetime

st.set_page_config(page_title="🔒 Painel de Exclusão - MARMORIZE")

st.title("🔒 Painel Restrito de Exclusão de Dados")

# Autenticação simples
senha = st.text_input("Digite a senha de acesso:", type="password")
if senha != "marmorize2025":
    st.warning("Acesso restrito. Digite a senha correta.")
    st.stop()

# Conexão com o banco
conn = sqlite3.connect("marmorize.db", check_same_thread=False)
c = conn.cursor()

# Cria tabela de log se não existir
c.execute("""
CREATE TABLE IF NOT EXISTS log_exclusoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT,
    tipo TEXT,
    funcionario TEXT,
    mes TEXT
)
""")
conn.commit()

# Função para registrar log
def registrar_log(tipo, funcionario, mes="-"):
    c.execute("INSERT INTO log_exclusoes (data, tipo, funcionario, mes) VALUES (?, ?, ?, ?)",
              (datetime.datetime.now().isoformat(), tipo, funcionario, mes))
    conn.commit()

# Exclusão de funcionário completo
st.subheader("Excluir Funcionário por Completo")
c.execute("SELECT nome FROM funcionarios")
funcs = [row[0] for row in c.fetchall()]

if funcs:
    func_sel = st.selectbox("Selecionar funcionário para exclusão completa", funcs, key="excluir_total")
    if st.button("Excluir Funcionário e todas as vendas", key="btn_excluir_total"):
        registrar_log("Exclusão Total", func_sel)
        c.execute("DELETE FROM funcionarios WHERE nome = ?", (func_sel,))
        c.execute("DELETE FROM metas_individuais WHERE nome = ?", (func_sel,))
        conn.commit()
        st.success(f"Funcionário '{func_sel}' e suas vendas foram excluídos com sucesso!")
else:
    st.info("Nenhum funcionário cadastrado para excluir.")

# Exclusão por mês específico
st.subheader("Excluir dados de vendas por Mês")
if funcs:
    func_mes = st.selectbox("Selecionar funcionário", funcs, key="func_mes")
    c.execute("SELECT DISTINCT mes FROM metas_individuais WHERE nome = ?", (func_mes,))
    meses = [row[0] for row in c.fetchall()]
    if meses:
        mes_excluir = st.selectbox("Selecionar mês para exclusão", meses)
        if st.button("Excluir vendas desse mês", key="btn_mes"):
            registrar_log("Exclusão Mensal", func_mes, mes_excluir)
            c.execute("DELETE FROM metas_individuais WHERE nome = ? AND mes = ?", (func_mes, mes_excluir))
            conn.commit()
            st.success(f"Vendas do mês '{mes_excluir}' para '{func_mes}' foram excluídas.")
    else:
        st.info("Funcionário não possui registros mensais.")

# Redefinir dados (zera vendas e metas)
st.subheader("Redefinir Vendas de Funcionário")
if funcs:
    func_reset = st.selectbox("Selecionar funcionário para zerar vendas", funcs, key="reset_func")
    if st.button("Zerar todas as vendas e metas", key="btn_reset"):
        registrar_log("Zeramento de Dados", func_reset)
        c.execute("DELETE FROM metas_individuais WHERE nome = ?", (func_reset,))
        conn.commit()
        st.success(f"Todas as vendas e metas de '{func_reset}' foram zeradas.")

# Visualização do log
st.subheader("📄 Histórico de Exclusões")
df_log = pd.read_sql_query("SELECT * FROM log_exclusoes ORDER BY id DESC", conn)
if not df_log.empty:
    df_log["data"] = pd.to_datetime(df_log["data"]).dt.strftime("%d/%m/%Y %H:%M")
    st.dataframe(df_log, use_container_width=True)
else:
    st.info("Nenhuma exclusão registrada até agora.")
