import streamlit as st
import os
from pathlib import Path
import sys
import json
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from core.workflow_engine import WorkflowEngine
from ui.components import display_analysis_result, display_function_info, display_repository_stats

st.set_page_config(
    page_title="Code Analysis Bot",
    page_icon="🔍",
    layout="wide"
)

def main():
    st.title("Code Analysis Bot")
    st.markdown("Analyze code issues using AI-powered function search and analysis")
    
    if 'workflow_engine' not in st.session_state:
        st.session_state.workflow_engine = None
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    
    with st.sidebar:
        st.header("Configuration")
        
        embedding_service = st.selectbox(
            "Embedding Service",
            ["openai", "ollama", "perplexity"],
            index=0
        )
        
        llm_service = st.selectbox(
            "LLM Service",
            ["openai", "perplexity", "ollama"],
            index=0
        )
        
        if st.button("Initialize Services"):
            with st.spinner("Initializing services..."):
                try:
                    st.session_state.workflow_engine = WorkflowEngine(
                        embedding_service_type=embedding_service,
                        llm_service_type=llm_service
                    )
                    
                    # Validate services
                    validation = st.session_state.workflow_engine.validate_services()
                    failed_services = [k for k, v in validation.items() if not v]
                    
                    if failed_services:
                        st.warning(f"Some services failed validation: {failed_services}")
                        st.info("Check your API keys and service configurations")
                    else:
                        st.success("All services validated successfully!")
                    
                    st.success("Services initialized successfully!")
                except Exception as e:
                    st.error(f"Failed to initialize services: {str(e)}")
        
        # Analysis History in Sidebar
        if st.session_state.workflow_engine:
            st.header("Analysis History")
            
            history_stats = st.session_state.workflow_engine.get_analysis_history_stats()
            st.metric("Total Analyses", history_stats.get("total_analyses", 0))
            
            if history_stats.get("total_analyses", 0) > 0:
                st.metric("Average Confidence", f"{history_stats.get('average_confidence', 0):.2f}")
                
                if st.button("View Recent Analyses"):
                    recent_analyses = st.session_state.workflow_engine.get_recent_analyses(5)
                    
                    if recent_analyses:
                        st.subheader("Recent Analyses")
                        for analysis in recent_analyses:
                            with st.expander(f"{analysis['timestamp'][:19]}: {analysis['query'][:30]}..."):
                                st.write(f"**Query:** {analysis['query']}")
                                st.write(f"**Enhanced:** {analysis['enhanced_query']}")
                                st.write(f"**Confidence:** {analysis['confidence_score']:.2f}")
                                st.write(f"**Services:** {analysis['services_used']['embedding']} + {analysis['services_used']['llm']}")
                                with st.expander("Analysis Result"):
                                    st.write(analysis['analysis_result'][:500] + "..." if len(analysis['analysis_result']) > 500 else analysis['analysis_result'])
                
                if st.button("Export History"):
                    output_file = f"analysis_history_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    st.session_state.workflow_engine.history_manager.export_history(output_file)
                    st.success(f"History exported to {output_file}")
    
    tab1, tab2, tab3 = st.tabs(["Repository Processing", "Issue Analysis", "Function Lookup"])
    
    with tab1:
        st.header("Process Repository")
        st.markdown("Extract functions and create embeddings from a repository")
        
        repo_path = st.text_input(
            "Repository Path",
            placeholder="/path/to/your/repository",
            help="Enter the full path to your repository"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            process_btn = st.button("Process Repository", disabled=not st.session_state.workflow_engine)
        
        with col2:
            if st.session_state.processing_complete:
                st.success("Repository processed!")
        
        if process_btn:
            if not repo_path:
                st.error("Please enter a repository path")
            elif not os.path.exists(repo_path):
                st.error("Repository path does not exist")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                with st.spinner("Processing repository... This may take a few minutes."):
                    try:
                        status_text.text("Extracting functions from repository...")
                        progress_bar.progress(25)
                        
                        result = st.session_state.workflow_engine.process_repository(repo_path)
                        
                        progress_bar.progress(100)
                        status_text.text("Processing complete!")
                        st.session_state.processing_complete = True
                        
                        st.success("Repository processed successfully!")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Functions", result["total_functions"])
                        with col2:
                            st.metric("Embedded Functions", result["embedded_functions"])
                        with col3:
                            st.metric("Success Rate", 
                                    f"{(result['embedded_functions']/result['total_functions']*100):.1f}%" 
                                    if result["total_functions"] > 0 else "0%")
                        
                        display_repository_stats(result["summary"])
                        
                    except Exception as e:
                        st.error(f"Error processing repository: {str(e)}")
                        st.info("Please check:")
                        st.info("- Repository path is correct and contains Python files")
                        st.info("- OpenSearch is running on localhost:9200")
                        st.info("- API keys are configured in .env file")
    
    with tab2:
        st.header("Analyze Issue")
        st.markdown("Describe your code issue and get AI-powered analysis")
        
        if not st.session_state.processing_complete:
            st.warning("Please process a repository first in the 'Repository Processing' tab")
            return
        
        user_query = st.text_area(
            "Describe your issue",
            placeholder="e.g., Authentication function is throwing errors when validating JWT tokens",
            height=100
        )
        
        with st.expander("Additional Context (Optional)"):
            repo_name = st.text_input("Repository Name")
            tech_stack = st.text_input("Tech Stack (comma-separated)")
            priority = st.selectbox("Priority", ["low", "medium", "high", "critical"])
            
            context = {}
            if repo_name:
                context["repo_name"] = repo_name
            if tech_stack:
                context["tech_stack"] = [t.strip() for t in tech_stack.split(",")]
            if priority:
                context["priority"] = priority
        
        if st.button("Analyze Issue", disabled=not st.session_state.workflow_engine):
            if not user_query:
                st.error("Please describe your issue")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                with st.spinner("Analyzing issue... This may take a minute."):
                    try:
                        status_text.text("Enhancing query...")
                        progress_bar.progress(20)
                        
                        status_text.text("Searching for relevant functions...")
                        progress_bar.progress(40)
                        
                        status_text.text("Analyzing with AI...")
                        progress_bar.progress(70)
                        
                        result = st.session_state.workflow_engine.analyze_user_issue(user_query, context)
                        
                        progress_bar.progress(100)
                        status_text.text("Analysis complete!")
                        
                        display_analysis_result(result)
                        
                    except Exception as e:
                        st.error(f"Error analyzing issue: {str(e)}")
    
    with tab3:
        st.header("Function Lookup Export")
        st.markdown("Export function lookup table and manage function data")
        
        if not st.session_state.processing_complete:
            st.warning("Please process a repository first")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox("Export Format", ["json", "csv"])
            
        with col2:
            if st.button("Export Function Lookup Table"):
                try:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"function_lookup_{timestamp}.{export_format}"
                    
                    st.session_state.workflow_engine.export_function_lookup_table(filename, export_format)
                    
                    st.success(f"Function lookup table exported to {filename}")
                    
                    # Show download info
                    st.info(f"File saved in the current directory: {filename}")
                    
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")
        
        # Display function statistics
        if st.session_state.workflow_engine and st.session_state.workflow_engine.lookup_table.lookup_df is not None:
            summary = st.session_state.workflow_engine.lookup_table.get_table_summary()
            display_repository_stats(summary)

if __name__ == "__main__":
    main()
