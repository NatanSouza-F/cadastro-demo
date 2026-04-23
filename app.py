"""
Plataforma de Cadastro Inteligente para Escritório Contábil
MVP desenvolvido com Streamlit para demonstração de conceito.
Autor: [Seu Nome]
Data: 2025
"""

import streamlit as st
import requests
import json
import os
import re
from datetime import datetime
from typing import Dict, Any

# =============================================================================
# CONFIGURAÇÕES DA PÁGINA
# =============================================================================
st.set_page_config(
    page_title="Cadastro Inteligente - Contabilidade",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================================================
# INICIALIZAÇÃO DO ESTADO DA SESSÃO
# =============================================================================
def init_session_state():
    """Inicializa todas as variáveis de sessão necessárias."""
    defaults = {
        'step': 0,                       # Etapa atual do wizard
        'perfil': None,                 # 'PJ' ou 'PF'
        'dados_cadastrais': {},         # Dados coletados na etapa 1
        'dados_operacionais': {},       # Dados da etapa 2
        'documentos': [],               # Lista de arquivos enviados
        'honorario_estimado': 0.0,      # Valor calculado
        'consulta_realizada': False     # Flag para controle de UI
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# =============================================================================
# FUNÇÕES DE CONSULTA A APIS (COM CACHE)
# =============================================================================
@st.cache_data(ttl=600, show_spinner=False)
def consulta_cnpj(cnpj: str) -> Dict[str, Any]:
    """
    Consulta dados do CNPJ na BrasilAPI.
    Retorna dicionário com dados da empresa ou None se falhar.
    """
    cnpj_clean = re.sub(r'\D', '', cnpj)
    if len(cnpj_clean) != 14:
        return None
    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_clean}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.warning(f"Não foi possível consultar o CNPJ automaticamente. Erro: {e}")
        return None

@st.cache_data(ttl=600, show_spinner=False)
def consulta_cep(cep: str) -> Dict[str, Any]:
    """
    Consulta endereço pelo CEP na BrasilAPI.
    """
    cep_clean = re.sub(r'\D', '', cep)
    if len(cep_clean) != 8:
        return None
    url = f"https://brasilapi.com.br/api/cep/v1/{cep_clean}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.warning(f"Não foi possível consultar o CEP. Erro: {e}")
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def consulta_cnae(codigo: str) -> str:
    """
    Retorna a descrição do CNAE.
    """
    if not codigo:
        return ""
    codigo_clean = re.sub(r'\D', '', codigo)
    url = f"https://brasilapi.com.br/api/cnae/v1/{codigo_clean}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('descricao', 'CNAE não encontrado')
    except:
        return "Descrição não disponível"

# =============================================================================
# FUNÇÕES DE CÁLCULO DE HONORÁRIOS
# =============================================================================
def calcular_honorario_pj(dados: Dict[str, Any]) -> float:
    """
    Calcula o honorário mensal estimado para Pessoa Jurídica.
    Baseado em: regime, faturamento, volume de notas, complexidade.
    """
    regime = dados.get('regime', 'Simples Nacional')
    faturamento = float(dados.get('faturamento', 0))
    num_notas = int(dados.get('num_notas', 0))
    tem_funcionarios = dados.get('tem_funcionarios', False)
    tem_estoque = dados.get('tem_estoque', False)
    situacao = dados.get('situacao_fiscal', 'regular')
    
    # Honorário base por regime
    base_dict = {
        'MEI': 150.0,
        'Simples Nacional': 600.0,
        'Lucro Presumido': 1200.0,
        'Lucro Real': 2200.0
    }
    base = base_dict.get(regime, 600.0)
    
    # Fator faturamento (faixas)
    if faturamento <= 10000:
        fator_fat = 0.8
    elif faturamento <= 30000:
        fator_fat = 1.0
    elif faturamento <= 100000:
        fator_fat = 1.4
    elif faturamento <= 300000:
        fator_fat = 1.8
    else:
        fator_fat = 2.5
    
    # Adicionais por complexidade
    add_notas = (num_notas // 20) * 80   # a cada 20 notas, +R$80
    add_func = 250.0 if tem_funcionarios else 0.0
    add_estoque = 200.0 if tem_estoque else 0.0
    
    # Penalidade por situação irregular (30% de acréscimo)
    fator_irregular = 1.3 if situacao == 'irregular' else 1.0
    
    honorario = (base * fator_fat + add_notas + add_func + add_estoque) * fator_irregular
    return round(honorario, 2)

def calcular_honorario_pf(dados: Dict[str, Any]) -> float:
    """
    Cálculo simplificado para Pessoa Física.
    Considera renda mensal, quantidade de bens e complexidade.
    """
    renda_mensal = float(dados.get('renda_mensal', 0))
    possui_bens = dados.get('possui_bens', False)
    possui_investimentos = dados.get('possui_investimentos', False)
    
    base = 200.0  # Honorário mínimo para IRPF simples
    if renda_mensal <= 5000:
        fator = 1.0
    elif renda_mensal <= 15000:
        fator = 1.5
    else:
        fator = 2.0
    
    extras = 0.0
    if possui_bens:
        extras += 100.0
    if possui_investimentos:
        extras += 150.0
        
    return round(base * fator + extras, 2)

# =============================================================================
# FUNÇÕES AUXILIARES DE VALIDAÇÃO
# =============================================================================
def validar_cnpj(cnpj: str) -> bool:
    """Validação simples de formato do CNPJ (14 dígitos)."""
    cnpj_clean = re.sub(r'\D', '', cnpj)
    return len(cnpj_clean) == 14

def validar_cpf(cpf: str) -> bool:
    """Valida formato do CPF (11 dígitos)."""
    cpf_clean = re.sub(r'\D', '', cpf)
    return len(cpf_clean) == 11

# =============================================================================
# INTERFACE DO USUÁRIO
# =============================================================================
def main():
    st.title("🧾 Plataforma de Cadastro Inteligente")
    st.caption("Preencha os dados para receber uma estimativa de honorários contábeis personalizada.")
    
    # Barra de progresso
    progresso = st.progress((st.session_state.step) / 3)
    
    # Controle das etapas do wizard
    if st.session_state.step == 0:
        etapa_selecao_perfil()
    elif st.session_state.step == 1:
        etapa_dados_cadastrais()
    elif st.session_state.step == 2:
        etapa_dados_operacionais()
    elif st.session_state.step == 3:
        etapa_upload()
    elif st.session_state.step == 4:
        etapa_resumo()
    
    # Atualiza barra de progresso
    progresso.progress(st.session_state.step / 4)

def etapa_selecao_perfil():
    """Etapa 0: Seleção do tipo de cliente."""
    st.header("Bem-vindo!")
    st.subheader("Selecione o tipo de cliente:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏢 Pessoa Jurídica", use_container_width=True):
            st.session_state.perfil = 'PJ'
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("👤 Pessoa Física", use_container_width=True):
            st.session_state.perfil = 'PF'
            st.session_state.step = 1
            st.rerun()

def etapa_dados_cadastrais():
    """Etapa 1: Dados cadastrais básicos com consulta automática."""
    st.header("📋 Dados Cadastrais")
    perfil = st.session_state.perfil
    
    # Container para formulário
    with st.container():
        if perfil == 'PJ':
            st.subheader("Dados da Empresa")
            col1, col2 = st.columns(2)
            with col1:
                cnpj_input = st.text_input(
                    "CNPJ", 
                    placeholder="00.000.000/0000-00",
                    value=st.session_state.dados_cadastrais.get('cnpj', ''),
                    key='cnpj_input'
                )
                # Botão de consulta
                if st.button("🔍 Consultar CNPJ", type="secondary"):
                    if validar_cnpj(cnpj_input):
                        with st.spinner("Consultando Receita Federal..."):
                            dados = consulta_cnpj(cnpj_input)
                            if dados:
                                st.session_state.dados_cadastrais.update({
                                    'cnpj': cnpj_input,
                                    'razao_social': dados.get('razao_social', ''),
                                    'nome_fantasia': dados.get('nome_fantasia', ''),
                                    'natureza_juridica': dados.get('natureza_juridica', {}).get('descricao', ''),
                                    'cnae_principal': dados.get('cnae_fiscal_descricao', ''),
                                    'cnae_codigo': dados.get('cnae_fiscal', ''),
                                    'cep': dados.get('cep', ''),
                                    'logradouro': dados.get('logradouro', ''),
                                    'bairro': dados.get('bairro', ''),
                                    'municipio': dados.get('municipio', ''),
                                    'uf': dados.get('uf', '')
                                })
                                st.success("CNPJ consultado com sucesso!")
                                st.rerun()
                            else:
                                st.error("CNPJ não encontrado ou erro na consulta.")
                    else:
                        st.error("CNPJ inválido! São necessários 14 dígitos.")

            # Campos preenchíveis manualmente (já preenchidos se a API retornou dados)
            dados = st.session_state.dados_cadastrais
            with col1:
                razao_social = st.text_input("Razão Social*", value=dados.get('razao_social', ''), key='razao_social')
                nome_fantasia = st.text_input("Nome Fantasia", value=dados.get('nome_fantasia', ''), key='nome_fantasia')
                natureza_juridica = st.text_input("Natureza Jurídica", value=dados.get('natureza_juridica', ''), key='natureza')
                cnae_principal = st.text_input("CNAE Principal", value=dados.get('cnae_principal', ''), key='cnae')
            with col2:
                # CEP
                cep_input = st.text_input("CEP", value=dados.get('cep', ''), key='cep_input')
                if st.button("📍 Buscar CEP"):
                    if len(re.sub(r'\D', '', cep_input)) == 8:
                        with st.spinner("Buscando endereço..."):
                            endereco = consulta_cep(cep_input)
                            if endereco:
                                st.session_state.dados_cadastrais.update({
                                    'cep': cep_input,
                                    'logradouro': endereco.get('street', ''),
                                    'bairro': endereco.get('neighborhood', ''),
                                    'municipio': endereco.get('city', ''),
                                    'uf': endereco.get('state', '')
                                })
                                st.rerun()
                    else:
                        st.error("CEP inválido.")
                logradouro = st.text_input("Logradouro", value=dados.get('logradouro', ''), key='logradouro')
                bairro = st.text_input("Bairro", value=dados.get('bairro', ''), key='bairro')
                municipio = st.text_input("Município", value=dados.get('municipio', ''), key='municipio')
                uf = st.text_input("UF", value=dados.get('uf', ''), key='uf', max_chars=2)
            
            # Atualiza dados no dicionário sempre que perder foco
            st.session_state.dados_cadastrais.update({
                'cnpj': cnpj_input,
                'razao_social': razao_social,
                'nome_fantasia': nome_fantasia,
                'natureza_juridica': natureza_juridica,
                'cnae_principal': cnae_principal,
                'cep': cep_input,
                'logradouro': logradouro,
                'bairro': bairro,
                'municipio': municipio,
                'uf': uf
            })
            
        else:  # Pessoa Física
            st.subheader("Dados da Pessoa Física")
            col1, col2 = st.columns(2)
            with col1:
                cpf = st.text_input("CPF*", placeholder="000.000.000-00", 
                                    value=st.session_state.dados_cadastrais.get('cpf', ''), key='cpf')
                nome = st.text_input("Nome Completo*", value=st.session_state.dados_cadastrais.get('nome', ''), key='nome')
                data_nascimento = st.date_input("Data de Nascimento", key='data_nasc')
            with col2:
                cep = st.text_input("CEP", value=st.session_state.dados_cadastrais.get('cep', ''), key='cep_pf')
                if st.button("📍 Buscar CEP", key='buscar_cep_pf'):
                    if len(re.sub(r'\D', '', cep)) == 8:
                        endereco = consulta_cep(cep)
                        if endereco:
                            st.session_state.dados_cadastrais.update({
                                'cep': cep,
                                'logradouro': endereco.get('street', ''),
                                'bairro': endereco.get('neighborhood', ''),
                                'municipio': endereco.get('city', ''),
                                'uf': endereco.get('state', '')
                            })
                            st.rerun()
                logradouro = st.text_input("Logradouro", value=st.session_state.dados_cadastrais.get('logradouro', ''), key='logradouro_pf')
                bairro = st.text_input("Bairro", value=st.session_state.dados_cadastrais.get('bairro', ''), key='bairro_pf')
                municipio = st.text_input("Município", value=st.session_state.dados_cadastrais.get('municipio', ''), key='municipio_pf')
                uf = st.text_input("UF", value=st.session_state.dados_cadastrais.get('uf', ''), key='uf_pf', max_chars=2)
            
            st.session_state.dados_cadastrais.update({
                'cpf': cpf,
                'nome': nome,
                'data_nascimento': data_nascimento.strftime('%d/%m/%Y') if data_nascimento else '',
                'cep': cep,
                'logradouro': logradouro,
                'bairro': bairro,
                'municipio': municipio,
                'uf': uf
            })
        
        # Navegação
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if st.button("⬅ Voltar", use_container_width=True):
                st.session_state.step = 0
                st.rerun()
        with col_btn2:
            if st.button("Próximo ➡", type="primary", use_container_width=True):
                # Validações mínimas
                if perfil == 'PJ':
                    if not validar_cnpj(st.session_state.dados_cadastrais.get('cnpj', '')):
                        st.error("CNPJ obrigatório e deve conter 14 dígitos.")
                    else:
                        st.session_state.step = 2
                        st.rerun()
                else:
                    if not validar_cpf(st.session_state.dados_cadastrais.get('cpf', '')):
                        st.error("CPF obrigatório e deve conter 11 dígitos.")
                    elif not st.session_state.dados_cadastrais.get('nome', ''):
                        st.error("Nome é obrigatório.")
                    else:
                        st.session_state.step = 2
                        st.rerun()

def etapa_dados_operacionais():
    """Etapa 2: Dados operacionais e situação fiscal."""
    st.header("📊 Dados Operacionais e Fiscais")
    perfil = st.session_state.perfil
    
    # Inicializar dicionário se vazio
    if not st.session_state.dados_operacionais:
        st.session_state.dados_operacionais = {}
    
    with st.form(key='form_operacional'):
        if perfil == 'PJ':
            st.subheader("Regime e Atividade")
            col1, col2, col3 = st.columns(3)
            with col1:
                regime = st.selectbox(
                    "Regime Tributário Atual*",
                    ["Simples Nacional", "Lucro Presumido", "Lucro Real", "MEI"],
                    index=["Simples Nacional", "Lucro Presumido", "Lucro Real", "MEI"].index(
                        st.session_state.dados_operacionais.get('regime', 'Simples Nacional')
                    )
                )
            with col2:
                faturamento = st.number_input(
                    "Faturamento médio mensal (R$)*",
                    min_value=0.0,
                    step=1000.0,
                    format="%.2f",
                    value=float(st.session_state.dados_operacionais.get('faturamento', 0))
                )
            with col3:
                num_notas = st.number_input(
                    "Nº médio de notas fiscais/mês*",
                    min_value=0,
                    step=1,
                    value=int(st.session_state.dados_operacionais.get('num_notas', 0))
                )
            
            st.subheader("Complexidade")
            col1, col2, col3 = st.columns(3)
            with col1:
                tem_funcionarios = st.checkbox(
                    "Possui funcionários?",
                    value=st.session_state.dados_operacionais.get('tem_funcionarios', False)
                )
            with col2:
                tem_estoque = st.checkbox(
                    "Controle de estoque / revenda de mercadorias?",
                    value=st.session_state.dados_operacionais.get('tem_estoque', False)
                )
            with col3:
                situacao_fiscal = st.radio(
                    "Situação fiscal*",
                    ["Em dia (regular)", "Com pendências/atrasos"],
                    index=0 if st.session_state.dados_operacionais.get('situacao_fiscal', 'regular') == 'regular' else 1,
                    horizontal=False
                )
            
            st.subheader("Contato e Expectativas")
            col1, col2 = st.columns(2)
            with col1:
                contato_nome = st.text_input(
                    "Nome do responsável*",
                    value=st.session_state.dados_operacionais.get('contato_nome', '')
                )
                contato_email = st.text_input(
                    "E-mail*",
                    value=st.session_state.dados_operacionais.get('contato_email', '')
                )
            with col2:
                contato_telefone = st.text_input(
                    "Telefone/WhatsApp",
                    value=st.session_state.dados_operacionais.get('contato_telefone', '')
                )
                expectativa = st.selectbox(
                    "Expectativa de início",
                    ["Imediato", "Próximo mês", "Em até 3 meses"]
                )
            
            # Botão de envio do formulário
            submitted = st.form_submit_button("Próximo ➡", type="primary", use_container_width=True)
            if submitted:
                # Validações
                if not contato_nome or not contato_email:
                    st.error("Nome e e-mail do responsável são obrigatórios.")
                else:
                    # Salva no session_state
                    st.session_state.dados_operacionais = {
                        'regime': regime,
                        'faturamento': faturamento,
                        'num_notas': num_notas,
                        'tem_funcionarios': tem_funcionarios,
                        'tem_estoque': tem_estoque,
                        'situacao_fiscal': 'regular' if 'Em dia' in situacao_fiscal else 'irregular',
                        'contato_nome': contato_nome,
                        'contato_email': contato_email,
                        'contato_telefone': contato_telefone,
                        'expectativa': expectativa
                    }
                    st.session_state.step = 3
                    st.rerun()
        
        else:  # Pessoa Física
            st.subheader("Rendimentos e Complexidade")
            col1, col2 = st.columns(2)
            with col1:
                renda_mensal = st.number_input(
                    "Renda mensal aproximada (R$)*",
                    min_value=0.0,
                    step=500.0,
                    format="%.2f",
                    value=float(st.session_state.dados_operacionais.get('renda_mensal', 0))
                )
                possui_bens = st.checkbox(
                    "Possui bens (imóveis, veículos)?",
                    value=st.session_state.dados_operacionais.get('possui_bens', False)
                )
            with col2:
                possui_investimentos = st.checkbox(
                    "Possui investimentos (ações, renda fixa, etc.)?",
                    value=st.session_state.dados_operacionais.get('possui_investimentos', False)
                )
                tipo_declaracao = st.radio(
                    "Tipo de declaração*",
                    ["Simplificada", "Completa"],
                    index=0 if st.session_state.dados_operacionais.get('tipo_declaracao', 'Simplificada') == 'Simplificada' else 1
                )
            
            contato_nome = st.text_input("Nome do responsável*", value=st.session_state.dados_operacionais.get('contato_nome', ''))
            contato_email = st.text_input("E-mail*", value=st.session_state.dados_operacionais.get('contato_email', ''))
            contato_telefone = st.text_input("Telefone/WhatsApp", value=st.session_state.dados_operacionais.get('contato_telefone', ''))
            
            submitted = st.form_submit_button("Próximo ➡", type="primary", use_container_width=True)
            if submitted:
                if not contato_nome or not contato_email:
                    st.error("Nome e e-mail são obrigatórios.")
                else:
                    st.session_state.dados_operacionais = {
                        'renda_mensal': renda_mensal,
                        'possui_bens': possui_bens,
                        'possui_investimentos': possui_investimentos,
                        'tipo_declaracao': tipo_declaracao,
                        'contato_nome': contato_nome,
                        'contato_email': contato_email,
                        'contato_telefone': contato_telefone
                    }
                    st.session_state.step = 3
                    st.rerun()
        
    # Navegação alternativa (voltar)
    if st.button("⬅ Voltar", key='voltar_op'):
        st.session_state.step = 1
        st.rerun()

def etapa_upload():
    """Etapa 3: Upload de documentos essenciais."""
    st.header("📎 Envio de Documentos")
    st.markdown("Para agilizar sua análise, anexe os documentos abaixo (formatos: PDF, JPG, PNG).")
    
    perfil = st.session_state.perfil
    
    if perfil == 'PJ':
        st.subheader("Documentos da Empresa")
        col1, col2 = st.columns(2)
        with col1:
            cartao_cnpj = st.file_uploader("Cartão CNPJ", type=['pdf', 'png', 'jpg', 'jpeg'], key='cartao')
            if cartao_cnpj:
                st.image(cartao_cnpj, width=200)
        with col2:
            contrato_social = st.file_uploader("Contrato Social ou Última Alteração", type=['pdf', 'png', 'jpg', 'jpeg'], key='contrato')
            if contrato_social:
                st.image(contrato_social, width=200)
        
        # Outros documentos opcionais
        procuracao = st.file_uploader("Procuração (se houver)", type=['pdf', 'png', 'jpg'], key='procuracao')
        
        documentos = [cartao_cnpj, contrato_social, procuracao]
    else:
        st.subheader("Documentos da Pessoa Física")
        col1, col2 = st.columns(2)
        with col1:
            rg_cpf = st.file_uploader("RG ou CNH", type=['pdf', 'png', 'jpg', 'jpeg'], key='rg')
            if rg_cpf:
                st.image(rg_cpf, width=200)
        with col2:
            comprovante_residencia = st.file_uploader("Comprovante de Residência", type=['pdf', 'png', 'jpg', 'jpeg'], key='comprovante')
            if comprovante_residencia:
                st.image(comprovante_residencia, width=200)
        
        ultima_declaracao = st.file_uploader("Última Declaração de IR (opcional)", type=['pdf'], key='dirpf')
        documentos = [rg_cpf, comprovante_residencia, ultima_declaracao]
    
    # Salva os documentos válidos na sessão
    st.session_state.documentos = [doc for doc in documentos if doc is not None]
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("⬅ Voltar", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    with col_btn2:
        if st.button("Gerar Proposta ➡", type="primary", use_container_width=True):
            # Calcula honorários
            if perfil == 'PJ':
                honorario = calcular_honorario_pj(st.session_state.dados_operacionais)
            else:
                honorario = calcular_honorario_pf(st.session_state.dados_operacionais)
            st.session_state.honorario_estimado = honorario
            st.session_state.step = 4
            st.rerun()

def etapa_resumo():
    """Etapa final: Exibe resumo e honorário calculado."""
    st.header("✅ Proposta Gerada com Sucesso!")
    st.balloons()
    
    perfil = st.session_state.perfil
    cad = st.session_state.dados_cadastrais
    op = st.session_state.dados_operacionais
    
    # Resumo em cards
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📌 Dados do Cliente")
        if perfil == 'PJ':
            st.write(f"**Razão Social:** {cad.get('razao_social', 'N/A')}")
            st.write(f"**CNPJ:** {cad.get('cnpj', '')}")
            st.write(f"**CNAE:** {cad.get('cnae_principal', '')}")
            st.write(f"**Regime:** {op.get('regime', '')}")
            st.write(f"**Faturamento:** R$ {op.get('faturamento', 0):,.2f}")
        else:
            st.write(f"**Nome:** {cad.get('nome', '')}")
            st.write(f"**CPF:** {cad.get('cpf', '')}")
            st.write(f"**Renda Mensal:** R$ {op.get('renda_mensal', 0):,.2f}")
    
    with col2:
        st.subheader("📋 Detalhes Operacionais")
        if perfil == 'PJ':
            st.write(f"**Notas/mês:** {op.get('num_notas', 0)}")
            st.write(f"**Funcionários:** {'Sim' if op.get('tem_funcionarios') else 'Não'}")
            st.write(f"**Estoque:** {'Sim' if op.get('tem_estoque') else 'Não'}")
            st.write(f"**Situação Fiscal:** {op.get('situacao_fiscal', '').capitalize()}")
        else:
            st.write(f"**Possui bens:** {'Sim' if op.get('possui_bens') else 'Não'}")
            st.write(f"**Investimentos:** {'Sim' if op.get('possui_investimentos') else 'Não'}")
            st.write(f"**Declaração:** {op.get('tipo_declaracao', '')}")
    
    # Honorário
    st.markdown("---")
    st.subheader("💰 Honorário Mensal Estimado")
    valor = st.session_state.honorario_estimado
    st.metric(label="Valor sugerido", value=f"R$ {valor:,.2f}")
    st.caption("*Valor estimado com base nas informações fornecidas. Sujeito a análise detalhada.")
    
    # Documentos enviados
    if st.session_state.documentos:
        st.markdown("---")
        st.subheader("📎 Documentos Anexados")
        for doc in st.session_state.documentos:
            st.write(f"- {doc.name} ({doc.size} bytes)")
    
    # Botões finais
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Reiniciar Cadastro", use_container_width=True):
            # Limpa session_state
            for key in ['step', 'perfil', 'dados_cadastrais', 'dados_operacionais', 'documentos', 'honorario_estimado']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    with col2:
        # Exportar dados como JSON
        dados_exportar = {
            'perfil': perfil,
            'cadastrais': cad,
            'operacionais': {k: str(v) for k, v in op.items()},  # converte tudo para string para JSON
            'honorario': valor,
            'data_geracao': datetime.now().isoformat()
        }
        json_str = json.dumps(dados_exportar, ensure_ascii=False, indent=4)
        st.download_button(
            label="📥 Baixar Resumo (JSON)",
            data=json_str,
            file_name=f"proposta_{cad.get('razao_social' if perfil == 'PJ' else 'nome', 'cliente').replace(' ', '_')}.json",
            mime="application/json",
            use_container_width=True
        )
    with col3:
        if st.button("📧 Enviar por E-mail", use_container_width=True):
            st.info("Funcionalidade de envio automático em desenvolvimento. Entre em contato pelo e-mail do escritório.")
            st.write(f"**E-mail cadastrado:** {op.get('contato_email', '')}")

# =============================================================================
# EXECUÇÃO PRINCIPAL
# =============================================================================
if __name__ == "__main__":
    main()
