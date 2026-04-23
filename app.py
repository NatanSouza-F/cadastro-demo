"""
BSB Contabilidade - Plataforma de Cadastro Inteligente
MVP Streamlit com tema neon escuro e UX imersiva.
"""

import streamlit as st
import requests
import json
import re
from datetime import datetime
from typing import Dict, Any

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================
st.set_page_config(
    page_title="BSB Contabilidade | Cadastro",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================================================
# CSS NEON ESCURO (NÍVEL NASA)
# =============================================================================
st.markdown("""
<style>
    /* Fundo principal com gradiente escuro e textura sutil */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #111111 100%);
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }

    /* Cabeçalho principal com efeito neon */
    h1 {
        color: #00f2fe;
        text-shadow: 0 0 10px #00f2fe, 0 0 20px #4facfe;
        font-weight: 800;
        letter-spacing: -0.5px;
    }

    h2, h3, .stSubheader {
        color: #7bffe0;
        text-shadow: 0 0 5px #7bffe0;
    }

    /* Cartões com borda neon suave e vidro */
    .stContainer, div[data-testid="stExpander"], div[data-testid="stForm"] {
        background: rgba(20, 20, 30, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        border: 1px solid rgba(0, 242, 254, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.8);
        padding: 20px;
    }

    /* Botões com efeito neon pulsante */
    .stButton > button {
        background: linear-gradient(145deg, #0a0a0a, #1a1a2e);
        border: 2px solid #00f2fe;
        color: #00f2fe;
        border-radius: 10px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        box-shadow: 0 0 10px #00f2fe33;
    }
    .stButton > button:hover {
        background: #00f2fe;
        color: #0a0a0a;
        box-shadow: 0 0 25px #00f2fe;
        transform: translateY(-2px);
    }

    /* Campos de entrada */
    input, textarea, select, .stNumberInput input {
        background: #0d0d1a !important;
        border: 1px solid #00f2fe66 !important;
        color: #e0e0e0 !important;
        border-radius: 8px !important;
    }
    input:focus {
        border-color: #00f2fe !important;
        box-shadow: 0 0 15px #00f2fe80 !important;
    }

    /* Radio e checkbox */
    .stRadio > div, .stCheckbox > label {
        color: #cccccc !important;
    }

    /* Métricas com glow */
    [data-testid="stMetricValue"] {
        color: #00f2fe;
        text-shadow: 0 0 8px #00f2fe;
    }

    /* Progress bar */
    .stProgress > div > div {
        background-color: #00f2fe;
    }

    /* Efeito de linhas de grade no fundo */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: linear-gradient(rgba(0,242,254,0.03) 1px, transparent 1px),
                          linear-gradient(90deg, rgba(0,242,254,0.03) 1px, transparent 1px);
        background-size: 40px 40px;
        pointer-events: none;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# INICIALIZAÇÃO DO ESTADO DA SESSÃO
# =============================================================================
def init_session_state():
    defaults = {
        'step': 0,
        'perfil': None,
        'dados_cadastrais': {},
        'dados_operacionais': {},
        'documentos': [],
        'honorario_interno': 0.0,  # Oculto do cliente
        'consulta_realizada': False
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
    cnpj_clean = re.sub(r'\D', '', cnpj)
    if len(cnpj_clean) != 14:
        return None
    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_clean}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except:
        return None

@st.cache_data(ttl=600, show_spinner=False)
def consulta_cep(cep: str) -> Dict[str, Any]:
    cep_clean = re.sub(r'\D', '', cep)
    if len(cep_clean) != 8:
        return None
    url = f"https://brasilapi.com.br/api/cep/v1/{cep_clean}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except:
        return None

# =============================================================================
# CÁLCULO DE HONORÁRIOS (INTERNO, NÃO EXIBIDO AO CLIENTE)
# =============================================================================
def calcular_honorario_pj(dados: Dict[str, Any]) -> float:
    regime = dados.get('regime', 'Simples Nacional')
    faturamento = float(dados.get('faturamento', 0))
    num_notas = int(dados.get('num_notas', 0))
    tem_funcionarios = dados.get('tem_funcionarios', False)
    tem_estoque = dados.get('tem_estoque', False)
    situacao = dados.get('situacao_fiscal', 'regular')
    
    base_dict = {
        'MEI': 150.0,
        'Simples Nacional': 600.0,
        'Lucro Presumido': 1200.0,
        'Lucro Real': 2200.0
    }
    base = base_dict.get(regime, 600.0)
    
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
    
    add_notas = (num_notas // 20) * 80
    add_func = 250.0 if tem_funcionarios else 0.0
    add_estoque = 200.0 if tem_estoque else 0.0
    fator_irregular = 1.3 if situacao == 'irregular' else 1.0
    
    honorario = (base * fator_fat + add_notas + add_func + add_estoque) * fator_irregular
    return round(honorario, 2)

def calcular_honorario_pf(dados: Dict[str, Any]) -> float:
    renda_mensal = float(dados.get('renda_mensal', 0))
    possui_bens = dados.get('possui_bens', False)
    possui_investimentos = dados.get('possui_investimentos', False)
    
    base = 200.0
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
# FUNÇÕES AUXILIARES
# =============================================================================
def validar_cnpj(cnpj: str) -> bool:
    return len(re.sub(r'\D', '', cnpj)) == 14

def validar_cpf(cpf: str) -> bool:
    return len(re.sub(r'\D', '', cpf)) == 11

# =============================================================================
# INTERFACE DO USUÁRIO
# =============================================================================
def main():
    # SAUDAÇÃO DE BOAS-VINDAS (NEON)
    st.title("BSB CONTABILIDADE")
    st.markdown("### *Seu futuro fiscal começa aqui.*")
    st.markdown("---")
    
    progresso = st.progress(st.session_state.step / 3)
    
    if st.session_state.step == 0:
        etapa_selecao_perfil()
    elif st.session_state.step == 1:
        etapa_dados_cadastrais()
    elif st.session_state.step == 2:
        etapa_dados_operacionais()
    elif st.session_state.step == 3:
        etapa_upload()
    elif st.session_state.step == 4:
        etapa_sucesso()
    
    progresso.progress(st.session_state.step / 4)

def etapa_selecao_perfil():
    st.header("Nova Proposta")
    st.subheader("Para começarmos, selecione o tipo de cliente:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏢 PESSOA JURÍDICA", use_container_width=True):
            st.session_state.perfil = 'PJ'
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("👤 PESSOA FÍSICA", use_container_width=True):
            st.session_state.perfil = 'PF'
            st.session_state.step = 1
            st.rerun()

def etapa_dados_cadastrais():
    st.header("📋 Dados Cadastrais")
    perfil = st.session_state.perfil
    
    with st.container():
        if perfil == 'PJ':
            st.subheader("Dados da Empresa")
            col1, col2 = st.columns(2)
            with col1:
                cnpj_input = st.text_input("CNPJ", placeholder="00.000.000/0000-00", key='cnpj_input')
                if st.button("🔍 Consultar CNPJ", type="secondary"):
                    if validar_cnpj(cnpj_input):
                        with st.spinner("Conectando ao servidor da Receita..."):
                            dados = consulta_cnpj(cnpj_input)
                            if dados:
                                st.session_state.dados_cadastrais.update({
                                    'cnpj': cnpj_input,
                                    'razao_social': dados.get('razao_social', ''),
                                    'nome_fantasia': dados.get('nome_fantasia', ''),
                                    'natureza_juridica': dados.get('natureza_juridica', {}).get('descricao', ''),
                                    'cnae_principal': dados.get('cnae_fiscal_descricao', ''),
                                    'cep': dados.get('cep', ''),
                                    'logradouro': dados.get('logradouro', ''),
                                    'bairro': dados.get('bairro', ''),
                                    'municipio': dados.get('municipio', ''),
                                    'uf': dados.get('uf', '')
                                })
                                st.success("Empresa localizada!")
                                st.rerun()
                            else:
                                st.error("CNPJ inválido ou não encontrado.")
                    else:
                        st.error("CNPJ deve ter 14 dígitos.")
            with col2:
                pass
            
            dados = st.session_state.dados_cadastrais
            with col1:
                razao_social = st.text_input("Razão Social*", value=dados.get('razao_social', ''))
                nome_fantasia = st.text_input("Nome Fantasia", value=dados.get('nome_fantasia', ''))
                natureza_juridica = st.text_input("Natureza Jurídica", value=dados.get('natureza_juridica', ''))
                cnae_principal = st.text_input("CNAE Principal", value=dados.get('cnae_principal', ''))
            with col2:
                cep_input = st.text_input("CEP", value=dados.get('cep', ''), key='cep_input')
                if st.button("📍 Buscar CEP"):
                    if len(re.sub(r'\D', '', cep_input)) == 8:
                        with st.spinner("Procurando endereço..."):
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
                logradouro = st.text_input("Logradouro", value=dados.get('logradouro', ''))
                bairro = st.text_input("Bairro", value=dados.get('bairro', ''))
                municipio = st.text_input("Município", value=dados.get('municipio', ''))
                uf = st.text_input("UF", value=dados.get('uf', ''), max_chars=2)
            
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
        else:
            st.subheader("Dados da Pessoa Física")
            col1, col2 = st.columns(2)
            with col1:
                cpf = st.text_input("CPF*", placeholder="000.000.000-00", key='cpf')
                nome = st.text_input("Nome Completo*", key='nome')
                data_nascimento = st.date_input("Data de Nascimento")
            with col2:
                cep = st.text_input("CEP", key='cep_pf')
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
                logradouro = st.text_input("Logradouro", key='logradouro_pf')
                bairro = st.text_input("Bairro", key='bairro_pf')
                municipio = st.text_input("Município", key='municipio_pf')
                uf = st.text_input("UF", max_chars=2, key='uf_pf')
            
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
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("⬅ Voltar", use_container_width=True):
                st.session_state.step = 0
                st.rerun()
        with col_btn2:
            if st.button("Próximo ➡", type="primary", use_container_width=True):
                if perfil == 'PJ' and not validar_cnpj(st.session_state.dados_cadastrais.get('cnpj', '')):
                    st.error("CNPJ obrigatório e válido.")
                elif perfil == 'PF' and (not validar_cpf(st.session_state.dados_cadastrais.get('cpf', '')) or not nome):
                    st.error("CPF e Nome são obrigatórios.")
                else:
                    st.session_state.step = 2
                    st.rerun()

# (A etapa de dados operacionais permanece igual, apenas com CSS aplicado automaticamente)
# Inclua as funções etapa_dados_operacionais() e etapa_upload() do código anterior, 
# mas remova qualquer exibição de honorário do fluxo.

def etapa_dados_operacionais():
    st.header("📊 Configuração Fiscal")
    perfil = st.session_state.perfil
    if not st.session_state.dados_operacionais:
        st.session_state.dados_operacionais = {}
    
    with st.form(key='form_operacional'):
        if perfil == 'PJ':
            regime = st.selectbox("Regime Tributário*", ["Simples Nacional", "Lucro Presumido", "Lucro Real", "MEI"])
            faturamento = st.number_input("Faturamento médio mensal (R$)*", min_value=0.0, step=1000.0)
            num_notas = st.number_input("Notas fiscais emitidas por mês*", min_value=0, step=1)
            tem_funcionarios = st.checkbox("Possui funcionários?")
            tem_estoque = st.checkbox("Controle de estoque?")
            situacao_fiscal = st.radio("Situação fiscal*", ["Em dia", "Com pendências"])
            contato_nome = st.text_input("Nome do responsável*")
            contato_email = st.text_input("E-mail*")
            contato_telefone = st.text_input("Telefone")
            expectativa = st.selectbox("Início desejado", ["Imediato", "Próximo mês", "Em até 3 meses"])
            
            submitted = st.form_submit_button("Avançar ➡", use_container_width=True)
            if submitted:
                if not contato_nome or not contato_email:
                    st.error("Nome e e-mail são obrigatórios.")
                else:
                    st.session_state.dados_operacionais = {
                        'regime': regime,
                        'faturamento': faturamento,
                        'num_notas': num_notas,
                        'tem_funcionarios': tem_funcionarios,
                        'tem_estoque': tem_estoque,
                        'situacao_fiscal': 'irregular' if 'pendências' in situacao_fiscal else 'regular',
                        'contato_nome': contato_nome,
                        'contato_email': contato_email,
                        'contato_telefone': contato_telefone,
                        'expectativa': expectativa
                    }
                    st.session_state.step = 3
                    st.rerun()
        else:
            renda_mensal = st.number_input("Renda mensal aproximada (R$)*", min_value=0.0, step=500.0)
            possui_bens = st.checkbox("Possui bens?")
            possui_investimentos = st.checkbox("Possui investimentos?")
            tipo_declaracao = st.radio("Tipo de declaração*", ["Simplificada", "Completa"])
            contato_nome = st.text_input("Nome do responsável*")
            contato_email = st.text_input("E-mail*")
            contato_telefone = st.text_input("Telefone")
            
            submitted = st.form_submit_button("Avançar ➡", use_container_width=True)
            if submitted:
                if not contato_nome or not contato_email:
                    st.error("Nome e e-mail obrigatórios.")
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

def etapa_upload():
    st.header("📎 Documentos para Validação")
    perfil = st.session_state.perfil
    if perfil == 'PJ':
        cartao = st.file_uploader("Cartão CNPJ", type=['pdf', 'png', 'jpg'])
        contrato = st.file_uploader("Contrato Social", type=['pdf', 'png', 'jpg'])
        docs = [cartao, contrato]
    else:
        doc_id = st.file_uploader("RG ou CNH", type=['pdf', 'png', 'jpg'])
        comp_res = st.file_uploader("Comprovante de Residência", type=['pdf', 'png', 'jpg'])
        docs = [doc_id, comp_res]
    
    st.session_state.documentos = [d for d in docs if d]
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅ Voltar", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    with col2:
        if st.button("Finalizar Cadastro", type="primary", use_container_width=True):
            # Calcula honorários internamente sem exibir
            if perfil == 'PJ':
                st.session_state.honorario_interno = calcular_honorario_pj(st.session_state.dados_operacionais)
            else:
                st.session_state.honorario_interno = calcular_honorario_pf(st.session_state.dados_operacionais)
            st.session_state.step = 4
            st.rerun()

def etapa_sucesso():
    st.header("🚀 Cadastro Enviado com Sucesso!")
    st.balloons()
    st.success("Recebemos suas informações. Nossa equipe da **BSB Contabilidade** analisará os documentos e enviará uma proposta personalizada em até 24 horas.")
    st.info(f"Um resumo foi enviado para o e-mail cadastrado: {st.session_state.dados_operacionais.get('contato_email', '')}")
    # O honorário está em st.session_state.honorario_interno, acessível pelo contador no backend (não exposto aqui)
    if st.button("🔄 Nova Proposta"):
        for key in ['step', 'perfil', 'dados_cadastrais', 'dados_operacionais', 'documentos', 'honorario_interno']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    main()
