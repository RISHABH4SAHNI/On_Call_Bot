import streamlit as st
from typing import Dict, Any
import plotly.express as px
import pandas as pd

def display_analysis_result(result: Dict[str, Any]):
    if "error" in result:
        st.error(result["error"])
        return
    
    st.success("Analysis Complete!")
    
    # Main metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Functions Found", result.get("functions_found", 0))
    with col2:
        st.metric("Functions Analyzed", result.get("functions_analyzed", 0))
    with col3:
        confidence = result.get("confidence_score", 0)
        st.metric("Confidence Score", f"{confidence:.2f}")
        
        # Confidence indicator with color
        if confidence >= 0.8:
            st.success("🟢 High Confidence")
        elif confidence >= 0.6:
            st.warning("🟡 Medium Confidence")
        else:
            st.error("🔴 Low Confidence")
    
    # Query comparison
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Original Query")
        st.text_area("", value=result.get("query", ""), height=80, disabled=True)
    with col2:
        st.subheader("Enhanced Query")
        st.text_area("", value=result.get("enhanced_query", result.get("query", "")), height=80, disabled=True)
    
    # Analysis section with better formatting
    st.subheader("🔍 AI Analysis")
    analysis_text = result.get("analysis", "No analysis available")
    
    # Format analysis with sections if possible
    if "ANALYSIS:" in analysis_text:
        sections = analysis_text.split("ANALYSIS:")
        if len(sections) > 1:
            st.markdown(sections[1])
    else:
        st.markdown(analysis_text)
    
    # Relevant functions section
    if "search_results" in result and result["search_results"]:
        st.subheader("📋 Relevant Functions")
        
        # Create a summary chart
        if len(result["search_results"]) > 1:
            relevance_data = []
            for i, search_result in enumerate(result["search_results"], 1):
                relevance_data.append({
                    "Function": f"{search_result.function_metadata.name}",
                    "Relevance Score": search_result.relevance_score,
                    "File": search_result.function_metadata.file_path.split('/')[-1]
                })
            
            df = pd.DataFrame(relevance_data)
            fig = px.bar(df, x="Function", y="Relevance Score", 
                        title="Function Relevance Scores",
                        hover_data=["File"])
            st.plotly_chart(fig, use_container_width=True)
        
        for i, search_result in enumerate(result["search_results"], 1):
            relevance_emoji = "🔥" if search_result.relevance_score > 0.8 else "📌" if search_result.relevance_score > 0.5 else "📄"
            with st.expander(f"{relevance_emoji} Function {i}: {search_result.function_metadata.name} (Score: {search_result.relevance_score:.3f})"):
                display_function_info(search_result)

def display_function_info(search_result):
    if not hasattr(search_result, 'function_metadata'):
        st.error("Invalid search result format")
        return
        
    func = search_result.function_metadata
    
    # Function header with key info
    st.markdown(f"**{func.name}** {'(async)' if func.is_async else ''}")
    
    # Two-column layout for metadata
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📁 Location**")
        st.write(f"**File:** {func.file_path}")
        st.write(f"**Lines:** {func.start_line}-{func.end_line}")
        if func.class_context:
            st.write(f"**Class:** {func.class_context}")
        st.write(f"**Module:** {func.module_name}")
    
    with col2:
        st.markdown("**⚙️ Properties**")
        st.write(f"**Type:** {'⚡ Async' if func.is_async else '🔄 Sync'}")
        st.write(f"**Relevance:** {search_result.relevance_score:.3f}")
        if func.decorators:
            st.write(f"**Decorators:** {', '.join(func.decorators)}")
        if func.calls:
            st.write(f"**Calls:** {len(func.calls)} functions")
        
        error_handling = func.error_handling.get('has_try_catch', False)
        st.write(f"**Error Handling:** {'✅ Yes' if error_handling else '❌ No'}")
    
    # Function calls details
    if func.calls:
        with st.expander(f"📞 Function Calls ({len(func.calls)})"):
            # Show first 10 calls, then count
            display_calls = func.calls[:10]
            st.write(", ".join(display_calls))
            if len(func.calls) > 10:
                st.write(f"... and {len(func.calls) - 10} more")
    
    # Code section
    st.markdown("**💻 Source Code**")
    st.code(func.code, language="python")
    
    # Nested functions
    if hasattr(search_result, 'nested_functions') and search_result.nested_functions:
        st.markdown(f"**🔗 Nested Functions ({len(search_result.nested_functions)})**")
        
        for nested_id, nested_info in search_result.nested_functions.items():
            with st.expander(f"🔗 {nested_info['function_name']}"):
                st.write(f"**File:** {nested_info['file_path']}")
                st.write(f"**Lines:** {nested_info['start_line']}-{nested_info['end_line']}")
                st.code(nested_info['code'], language="python")

def display_repository_stats(stats: Dict[str, Any]):
    if not stats:
        st.info("No statistics available")
        return
        
    st.subheader("📊 Repository Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Functions", stats.get("total_functions", 0))
    with col2:
        st.metric("⚡ Async Functions", stats.get("async_functions", 0))
    with col3:
        st.metric("🛡️ With Error Handling", stats.get("functions_with_error_handling", 0))
    with col4:
        st.metric("📦 Unique Modules", stats.get("unique_modules", 0))
    
    # Create a pie chart if we have data
    if stats.get("total_functions", 0) > 0:
        chart_data = pd.DataFrame({
            "Type": ["Async Functions", "Sync Functions", "With Error Handling", "Without Error Handling"],
            "Count": [
                stats.get("async_functions", 0),
                stats.get("total_functions", 0) - stats.get("async_functions", 0),
                stats.get("functions_with_error_handling", 0),
                stats.get("total_functions", 0) - stats.get("functions_with_error_handling", 0)
            ]
        })
        
        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.pie(chart_data[:2], values="Count", names="Type", title="Function Types")
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.pie(chart_data[2:], values="Count", names="Type", title="Error Handling")
            st.plotly_chart(fig2, use_container_width=True)
