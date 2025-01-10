import streamlit as st
from utils import DocumentLoader, ChatManager, ChainManager, MANUAL_DIR

def initialize_page():
    if st.session_state.get("current_page") != "manual":
        st.session_state["current_page"] = "manual"
        # chain과 messages 모두 초기화
        for key in list(st.session_state.keys()):
            if key.endswith(("_chain", "_messages")) and not key.startswith("manual"):
                del st.session_state[key]

def run_manual_page():
    initialize_page()
    st.title("🧐매뉴얼 검색")
    st.markdown("""
    검색 예시: \"산모가 clindamycin을 사용 중인데 모유수유가 가능한가요?\", \"500g 아기의 적정 ET tube 깊이는?\"
    """)
    
    ChatManager.initialize_session_state("manual")
    
    with st.sidebar:
        clear_btn = st.button("대화초기화")
        selected_model = st.selectbox(
            "LLM 선택", ["gpt-4o", "gpt-4-turbo", "gpt-4o-mini"], index=0
        )
    
    if "manual_chain" not in st.session_state:
        st.session_state["manual_chain"] = None
    
    if st.session_state["manual_chain"] is None and not st.session_state["is_loading"]:
        try:
            st.session_state["is_loading"] = True
            # 여기서 empty 컨테이너를 생성
            status_container = st.empty()
            # 로딩 메시지 표시
            status_container.info("매뉴얼 문서를 로드하고 있습니다...")
            
            retriever = DocumentLoader.load_documents(MANUAL_DIR)
            if retriever is None:
                status_container.error("문서 로딩에 실패했습니다.")
                st.stop()
                
            chain = ChainManager.create_chain(retriever, model_name=selected_model)
            st.session_state["manual_chain"] = chain
            st.session_state["is_loading"] = False
            
            # 완료 메시지로 업데이트
            status_container.success("매뉴얼 로딩이 완료되었습니다!")
            
        except Exception as e:
            st.session_state["is_loading"] = False
            status_container.error(f"문서 로딩 중 오류가 발생했습니다: {str(e)}")
            st.stop()
    
    if clear_btn:
        ChatManager.clear_messages("manual")
    
    ChatManager.print_messages("manual")
    
    user_input = st.chat_input("매뉴얼에 대해 물어보세요")
    
    if user_input:
        chain = st.session_state["manual_chain"]
        st.chat_message("user").write(user_input)
        
        response = chain.stream(user_input)
        with st.chat_message("assistant"):
            container = st.empty()
            ai_answer = ""
            for token in response:
                ai_answer += token
                container.markdown(ai_answer)
        
        ChatManager.add_message("manual", "user", user_input)
        ChatManager.add_message("manual", "assistant", ai_answer)

if __name__ == "__main__":
    run_manual_page()