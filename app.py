import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

# =========================================================
# 1. 페이지 설정
# =========================================================
st.set_page_config(
    page_title="Smart Stock AI", 
    page_icon="📈", 
    layout="wide"
)

# [안내] 디자인(색상, 폰트 등)은 이제 .streamlit/config.toml 파일에서 관리합니다.
# 따라서 여기에 <style> 코드는 더 이상 필요 없습니다.

# =========================================================
# 2. 세션 상태 초기화
# =========================================================
if 'count_why' not in st.session_state: st.session_state.count_why = 3
if 'count_hojae' not in st.session_state: st.session_state.count_hojae = 2
if 'count_fund' not in st.session_state: st.session_state.count_fund = 3
if 'count_risk' not in st.session_state: st.session_state.count_risk = 2
if 'count_plan' not in st.session_state: st.session_state.count_plan = 3

# =========================================================
# 3. 핵심 로직 함수
# =========================================================
def calculate_rise_probability(data):
    score = 0
    reasons = []

    if data['current_price'] > data['ma_20']:
        score += 30
        reasons.append("📈 20일 이평선 상향 돌파 (+30점)")
    
    if 30 <= data['rsi'] <= 45:
        score += 30
        reasons.append("🌊 RSI 저점 매수 구간 (+30점)")
    elif data['rsi'] > 70:
        score -= 10
        reasons.append("🔥 RSI 과열 구간 (-10점)")

    if data['macd'] > data['macd_signal']:
        score += 20
        reasons.append("⚡ MACD 골든크로스 (+20점)")

    if data['volume'] > data['prev_volume']:
        score += 20
        reasons.append("📊 전일 대비 거래량 증가 (+20점)")

    final_prob = max(0, min(score, 100))
    return final_prob, reasons

def decide_sell_action(purchase_price, current_price, rise_probability):
    profit_rate = ((current_price - purchase_price) / purchase_price) * 100
    
    if profit_rate >= 10:
        if rise_probability >= 70:
            return "HOLD", "강력 보유", f"수익률 {profit_rate:.2f}%이나 상승확률이 {rise_probability}점으로 매우 높아 추가 상승을 기대함."
        else:
            return "SELL", "전량 매도(익절)", f"목표 수익률 {profit_rate:.2f}% 달성 및 상승 모멘텀 둔화로 이익 확정."
    elif profit_rate >= 7:
        if rise_probability >= 60:
            return "HOLD", "보유 지속", f"수익률 {profit_rate:.2f}% 진입, 상승 추세({rise_probability}점)가 유지되어 홀딩."
        else:
            return "SELL_PART", "분할 매도(20~30%)", f"수익률 {profit_rate:.2f}% 달성. 리스크 관리를 위해 일부 수익 실현."
    elif profit_rate >= 4.5:
        if rise_probability >= 60:
            return "HOLD", "관망(홀딩)", f"초기 수익권({profit_rate:.2f}%)이며 상승 시그널 존재."
        else:
            return "SELL_PART", "비중 축소", f"수익률 {profit_rate:.2f}%. 상승 탄력이 약해 비중 축소 권장."
    elif profit_rate <= -10:
        if rise_probability >= 65:
            return "HOLD", "손절 보류", f"현재 {profit_rate:.2f}% 손실 구간이나, 기술적 반등 확률({rise_probability}점)이 높아 대기."
        else:
            action = "전량 손절" if profit_rate <= -20 else "부분 손절"
            return "CUT", f"{action}", f"손실율 {profit_rate:.2f}% 확대 및 반등 모멘텀 부재로 리스크 차단."
    else:
        return "HOLD", "관망", f"현재 변동폭({profit_rate:.2f}%)이 기준치 이내이며 특이 신호 없음."

# =========================================================
# 4. 사이드바
# =========================================================
with st.sidebar:
    st.title("⚙️ 설정 및 API")
    user_api_key = ""
    try:
        if st.secrets and "general" in st.secrets and "stock_api_key" in st.secrets["general"]:
            user_api_key = st.secrets["general"]["stock_api_key"]
            st.success("API 키 로드 완료")
        else:
            st.info("수동 모드 (API 키 없음)")
            user_api_key = st.text_input("API Key", type="password")
    except:
        user_api_key = st.text_input("API Key", type="password")
    st.markdown("---")
    st.caption("Developed by Min Jung-woo")

# =========================================================
# 5. 메인 화면
# =========================================================
st.title("🤖 Smart Investment Assistant")
st.markdown("##### AI 기반 주식 분석 및 투자의향서 작성 시스템")

tab1, tab2, tab3 = st.tabs(["📈 주식 분석 대시보드", "🤖 AI 분석 보고서", "✍️ 투자의향서 작성"])

# --- TAB 1 ---
with tab1:
    with st.container(border=True):
        st.subheader("📌 데이터 입력")
        col1, col2, col3 = st.columns(3)
        with col1:
            stock_name = st.text_input("종목명 (티커)", value="IONQ")
            purchase_price = st.number_input("매수 평균가 ($)", value=15.0, step=0.1, format="%.2f")
        with col2:
            current_price = st.number_input("현재가 ($)", value=16.5, step=0.1, format="%.2f")
            ma_20 = st.number_input("20일 이동평균선", value=15.8, step=0.1)
        with col3:
            volume = st.number_input("금일 거래량", value=1500000)
            prev_volume = st.number_input("전일 거래량", value=1200000)
        with st.expander("보조지표 상세 입력"):
            c1, c2, c3 = st.columns(3)
            with c1: rsi = st.slider("RSI", 0, 100, 45)
            with c2: macd = st.number_input("MACD", value=0.5)
            with c3: macd_signal = st.number_input("MACD Signal", value=0.3)

    input_data = {
        "current_price": current_price, "ma_20": ma_20,
        "rsi": rsi, "macd": macd, "macd_signal": macd_signal,
        "volume": volume, "prev_volume": prev_volume
    }

    if st.button("🚀 AI 분석 실행", type="primary", use_container_width=True):
        prob_score, reasons = calculate_rise_probability(input_data)
        action_code, action_title, action_desc = decide_sell_action(purchase_price, current_price, prob_score)
        profit_rate = ((current_price - purchase_price) / purchase_price) * 100

        st.session_state['analysis_result'] = {
            "stock_name": stock_name,
            "purchase_price": purchase_price,
            "current_price": current_price,
            "profit_rate": profit_rate,
            "prob_score": prob_score,
            "reasons": reasons,
            "action_title": action_title,
            "action_desc": action_desc,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        st.divider()
        r_col1, r_col2 = st.columns([1, 2])
        with r_col1:
            fig = go.Figure(go.Indicator(
                mode = "gauge+number", value = prob_score, title = {'text': "상승 예측 확률"},
                gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#1976d2"},
                         'steps': [{'range': [0, 50], 'color': '#ffebee'}, {'range': [50, 70], 'color': '#fff3e0'}, {'range': [70, 100], 'color': '#e8f5e9'}],
                         'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': prob_score}}
            ))
            fig.update_layout(height=300, margin=dict(l=20,r=20,t=50,b=20))
            st.plotly_chart(fig, use_container_width=True)
        with r_col2:
            st.markdown(f"### 📢 판단 결과: **{action_title}**")
            
            # [수정] HTML 대신 Streamlit 전용 박스 사용 (깔끔함 + 보안경고 없음)
            if profit_rate > 0:
                st.success(f"▲ {profit_rate:.2f}% 수익 중")
            else:
                st.error(f"▼ {profit_rate:.2f}% 손실 중")
                
            st.markdown(f"**상세 분석:** {action_desc}")
            for r in reasons: st.markdown(f"- ✅ {r}")

# --- TAB 2 ---
with tab2:
    st.header("🤖 AI 분석 보고서")
    if 'analysis_result' in st.session_state:
        res = st.session_state['analysis_result']
        ai_report_text = f"""
[ AI 자동 분석 리포트 ]
작성일: {res['date']} | 종목: {res['stock_name']}
현재가: {res['current_price']} (수익률: {res['profit_rate']:.2f}%)
상승확률: {res['prob_score']}점
AI 판단: {res['action_title']}
"""
        st.text_area("AI 리포트 결과", value=ai_report_text, height=300)
    else:
        st.info("분석 결과가 없습니다.")

# --- TAB 3 ---
with tab3:
    # [수정] HTML 배너 대신 깔끔한 Info 박스로 교체
    st.info("✍️ **주식 투자 심의 계획서 (Investment Thesis)**\n\n본인의 투자 철학과 시나리오를 직접 기록하여 원칙을 지키세요.")
    
    default_ticker = st.session_state.get('analysis_result', {}).get('stock_name', '')
    default_price = st.session_state.get('analysis_result', {}).get('current_price', 0.0)

    col_t1, col_t2 = st.columns(2)
    with col_t1: f_date = st.date_input("작성일", datetime.now())
    with col_t2: f_author = st.text_input("작성자", value="민정우")
    col_t3, col_t4, col_t5 = st.columns(3)
    with col_t3: f_ticker = st.text_input("종목명 (티커)", value=default_ticker)
    with col_t4: f_price = st.number_input("현재 주가 ($)", value=float(default_price), step=0.1)
    with col_t5: f_period = st.selectbox("목표 보유 기간", ["단기 (1개월)", "중기 (6개월~1년)", "장기 (3년 이상)"])
    st.markdown("---")

    # 1. 아이디어
    st.subheader("1. 핵심 투자 아이디어 (The Why)")
    list_why = []
    for i in range(st.session_state.count_why):
        val = st.text_input(f"아이디어 {i+1}", key=f"why_{i}")
        if val: list_why.append(val)
    if st.button("➕ 아이디어 추가", key="btn_add_why"):
        st.session_state.count_why += 1
        st.rerun()
    st.markdown("---")

    # 2. 호재
    st.subheader("2. 호재 및 모멘텀 (Catalysts)")
    list_hojae = []
    for i in range(st.session_state.count_hojae):
        val = st.text_input(f"호재 {i+1}", key=f"hojae_{i}")
        if val: list_hojae.append(val)
    if st.button("➕ 호재 추가", key="btn_add_hojae"):
        st.session_state.count_hojae += 1
        st.rerun()
    st.markdown("---")

    # 3. 기업 분석
    st.subheader("3. 기업 분석 (Fundamental)")
    list_fund = []
    placeholders_fund = ["매출 성장 (예: 연 50% 성장)", "현금 흐름 (예: 2년치 확보)", "경쟁 우위 (예: 독점 기술)"]
    for i in range(st.session_state.count_fund):
        ph = placeholders_fund[i] if i < len(placeholders_fund) else f"추가 분석 {i+1}"
        val = st.text_input(f"분석 항목 {i+1}", placeholder=ph, key=f"fund_{i}")
        if val: list_fund.append(val)
    if st.button("➕ 분석 항목 추가", key="btn_add_fund"):
        st.session_state.count_fund += 1
        st.rerun()
    st.markdown("---")

    # 4. 리스크
    st.subheader("4. 리스크 분석 (Devil's Advocate) ⭐")
    list_risk = []
    for i in range(st.session_state.count_risk):
        val = st.text_input(f"악재/리스크 {i+1}", key=f"risk_{i}")
        if val: list_risk.append(val)
    if st.button("➕ 리스크 추가", key="btn_add_risk"):
        st.session_state.count_risk += 1
        st.rerun()
    f_risk_plan = st.selectbox("대응책 (리스크 발생 시)", ["과감히 손절한다", "비중을 축소한다", "오히려 추매한다", "관망한다"])
    st.markdown("---")

    # 5. 매매 시나리오
    st.subheader("5. 매매 시나리오 (Action Plan)")
    list_plan = []
    placeholders_plan = ["매수 전략 (예: 30% 선진입)", "익절 목표가 (예: $25)", "손절 라인 (예: $12)"]
    for i in range(st.session_state.count_plan):
        ph = placeholders_plan[i] if i < len(placeholders_plan) else f"추가 전략 {i+1}"
        val = st.text_input(f"전략 {i+1}", placeholder=ph, key=f"plan_{i}")
        if val: list_plan.append(val)
    if st.button("➕ 전략 항목 추가", key="btn_add_plan"):
        st.session_state.count_plan += 1
        st.rerun()
    st.markdown("---")

    # 6. 최종 결정
    st.subheader("6. 최종 결정 (Final Verdict)")
    f_verdict = st.radio("최종 판단을 선택하세요", ["매수 승인 (Strong Buy)", "조금 더 관망 (Watch)", "매수 불가 (Pass)"], horizontal=True)
    st.markdown("---")

    if st.button("📝 투자의향서 생성하기", type="primary", use_container_width=True):
        str_why = "\n".join([f"- {item}" for item in list_why])
        str_hojae = "\n".join([f"- {item}" for item in list_hojae])
        str_fund = "\n".join([f"- {item}" for item in list_fund])
        str_risk = "\n".join([f"- {item}" for item in list_risk])
        str_plan = "\n".join([f"- {item}" for item in list_plan])

        thesis_text = f"""# 📈 주식 투자 심의 계획서 (Investment Thesis)

**작성일:** {f_date.strftime('%Y년 %m월 %d일')}
**작성자:** {f_author}
**종목명 (티커):** {f_ticker}
**현재 주가:** ${f_price}
**목표 보유 기간:** {f_period}

---

## 1. 핵심 투자 아이디어 (The Why)
> "왜 하필 지금, 이 종목을 사야 하는가?"
{str_why}

## 2. 호재 및 모멘텀 (Catalysts)
> "주가를 끌어올릴 재료는 무엇인가?"
{str_hojae}

## 3. 기업 분석 (Fundamental)
> "이 회사의 기초 체력은?"
{str_fund}

## 4. 리스크 분석 (Devil's Advocate) [중요⭐]
> "내가 틀렸다면, 무엇 때문일까?"
{str_risk}
- **대응책:** {f_risk_plan}

## 5. 매매 시나리오 (Action Plan)
> "감정을 배제한 기계적 매매 전략"
{str_plan}

## 6. 최종 결정 (Final Verdict)
**□ {f_verdict}**

---
*작성자: 미래의 100K 자산가 {f_author}*
"""
        st.success("투자의향서가 생성되었습니다!")
        st.text_area("생성된 투자의향서", value=thesis_text, height=600)
        st.download_button(label="💾 다운로드 (.md)", data=thesis_text, file_name=f"Investment_Thesis_{f_ticker}_{f_date}.md", mime="text/markdown")