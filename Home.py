import streamlit as st
from utils import initialize_directories

def main():
    initialize_directories()
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = None
    
    st.title("🧐 SMC NICU Knowledge Hub")
    st.markdown("""
    이 지식허브에서는 다음과 같은 문서들을 검색할 수 있습니다🤪:
    
    - **Manual**: NICU 매뉴얼 문서 검색
    - **Problem Cases**: 환자 사례 검색
    - **Papers**: SMC 발표 논문 검색
    
    왼쪽 사이드바에서 원하시는 카테고리를 선택해주세요.
    
    제작: 성세인ㅋ

    """)

if __name__ == "__main__":
    main()