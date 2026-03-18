import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json
from collections import Counter
import re

# Page configuration
st.set_page_config(
    page_title="Contract Analysis Dashboard",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">📄 Contract Analysis Dashboard</h1>', unsafe_allow_html=True)
st.markdown("---")

# Paths
INPUT_DIR = Path("../Data/raw/full_contract_txt")
TRANSFORMED_DIR = Path("../Data/transformed")
ANALYSIS_DIR = Path("analysis_results")

@st.cache_data
def load_contract_stats():
    """Load contract statistics"""
    stats = []
    for file_path in INPUT_DIR.glob("*.txt"):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            stats.append({
                'contract_id': file_path.stem,
                'filename': file_path.name,
                'file_size_kb': file_path.stat().st_size / 1024,
                'word_count': len(content.split()),
                'char_count': len(content),
                'line_count': len(content.split('\n')),
                'content': content
            })
        except Exception as e:
            st.error(f"Error loading {file_path.name}: {e}")
    
    return pd.DataFrame(stats)

@st.cache_data
def extract_keywords(df, top_n=100):
    """Extract most frequent keywords"""
    all_text = ' '.join(df['content'].fillna(''))
    words = re.findall(r'\b[a-z]{3,}\b', all_text.lower())
    
    stop_words = {'the', 'and', 'for', 'with', 'that', 'this', 'from', 
                  'will', 'shall', 'are', 'was', 'were', 'been', 'has', 
                  'have', 'had', 'but', 'not', 'all', 'can', 'any', 'may',
                  'such', 'other', 'than', 'into', 'each', 'which', 'upon'}
    
    filtered = [w for w in words if w not in stop_words]
    return Counter(filtered).most_common(top_n)

# Load data
with st.spinner("Loading contract data..."):
    df_contracts = load_contract_stats()
    keywords = extract_keywords(df_contracts, top_n=100)

# Sidebar
with st.sidebar:
    st.header("📊 Quick Stats")
    st.metric("Total Contracts", len(df_contracts))
    st.metric("Total Words", f"{df_contracts['word_count'].sum():,}")
    st.metric("Avg Contract Length", f"{df_contracts['word_count'].mean():.0f} words")
    st.metric("Total Size", f"{df_contracts['file_size_kb'].sum():.1f} KB")
    
    st.markdown("---")
    
    st.header("🔍 Filters")
    min_words = st.slider(
        "Minimum Words",
        min_value=0,
        max_value=int(df_contracts['word_count'].max()),
        value=0,
        step=100
    )
    
    max_words = st.slider(
        "Maximum Words",
        min_value=0,
        max_value=int(df_contracts['word_count'].max()),
        value=int(df_contracts['word_count'].max()),
        step=100
    )
    
    # Apply filters
    df_filtered = df_contracts[
        (df_contracts['word_count'] >= min_words) & 
        (df_contracts['word_count'] <= max_words)
    ]

# Main content - Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Overview", 
    "📊 Visualizations", 
    "🔤 Keywords", 
    "📄 Contract Explorer",
    "📋 Data Table"
])

# TAB 1: Overview
with tab1:
    st.header("Contract Statistics Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(
            label="📁 Total Contracts",
            value=len(df_filtered),
            delta=f"{len(df_filtered) - len(df_contracts)} from total" if min_words > 0 or max_words < df_contracts['word_count'].max() else None
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(
            label="📝 Total Words",
            value=f"{df_filtered['word_count'].sum():,}"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(
            label="📏 Avg Length",
            value=f"{df_filtered['word_count'].mean():.0f} words"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(
            label="💾 Total Size",
            value=f"{df_filtered['file_size_kb'].sum():.1f} KB"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Distribution stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Word Count Distribution")
        stats_df = pd.DataFrame({
            'Statistic': ['Mean', 'Median', 'Min', 'Max', 'Std Dev'],
            'Value': [
                f"{df_filtered['word_count'].mean():.0f}",
                f"{df_filtered['word_count'].median():.0f}",
                f"{df_filtered['word_count'].min():.0f}",
                f"{df_filtered['word_count'].max():.0f}",
                f"{df_filtered['word_count'].std():.0f}"
            ]
        })
        st.dataframe(stats_df, hide_index=True, use_container_width=True)
    
    with col2:
        st.subheader("File Size Distribution (KB)")
        size_stats_df = pd.DataFrame({
            'Statistic': ['Mean', 'Median', 'Min', 'Max', 'Total'],
            'Value': [
                f"{df_filtered['file_size_kb'].mean():.2f}",
                f"{df_filtered['file_size_kb'].median():.2f}",
                f"{df_filtered['file_size_kb'].min():.2f}",
                f"{df_filtered['file_size_kb'].max():.2f}",
                f"{df_filtered['file_size_kb'].sum():.2f}"
            ]
        })
        st.dataframe(size_stats_df, hide_index=True, use_container_width=True)

# TAB 2: Visualizations
with tab2:
    st.header("Contract Analysis Visualizations")
    
    # Histogram
    st.subheader("📊 Contract Length Distribution")
    fig_hist = px.histogram(
        df_filtered,
        x='word_count',
        nbins=30,
        title='Distribution of Contract Lengths',
        labels={'word_count': 'Word Count', 'count': 'Frequency'},
        color_discrete_sequence=['#636EFA']
    )
    fig_hist.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig_hist, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Box plot
        st.subheader("📦 Text Length Distribution")
        fig_box = go.Figure()
        fig_box.add_trace(go.Box(
            y=df_filtered['word_count'],
            name='Word Count',
            marker_color='#EF553B',
            boxmean='sd'
        ))
        fig_box.update_layout(
            title='Contract Length Boxplot',
            yaxis_title='Word Count',
            height=400
        )
        st.plotly_chart(fig_box, use_container_width=True)
    
    with col2:
        # Scatter plot
        st.subheader("🔗 File Size vs Word Count")
        fig_scatter = px.scatter(
            df_filtered,
            x='file_size_kb',
            y='word_count',
            title='File Size vs Word Count Correlation',
            labels={'file_size_kb': 'File Size (KB)', 'word_count': 'Word Count'},
            color='word_count',
            color_continuous_scale='Viridis',
            trendline='ols'
        )
        fig_scatter.update_layout(height=400)
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Top contracts by length
    st.subheader("📑 Top 10 Longest Contracts")
    top_contracts = df_filtered.nlargest(10, 'word_count')[['filename', 'word_count', 'file_size_kb']]
    fig_bar = px.bar(
        top_contracts,
        x='word_count',
        y='filename',
        orientation='h',
        title='Top 10 Longest Contracts',
        labels={'word_count': 'Word Count', 'filename': 'Contract'},
        color='word_count',
        color_continuous_scale='Blues'
    )
    fig_bar.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

# TAB 3: Keywords
with tab3:
    st.header("Most Frequent Legal Terms & Keywords")
    
    # Number of keywords to show
    n_keywords = st.slider("Number of keywords to display", 10, 100, 20, step=5)
    
    top_keywords = keywords[:n_keywords]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Bar chart
        st.subheader(f"📊 Top {n_keywords} Keywords")
        keywords_df = pd.DataFrame(top_keywords, columns=['Keyword', 'Frequency'])
        fig_keywords = px.bar(
            keywords_df,
            x='Frequency',
            y='Keyword',
            orientation='h',
            title=f'Top {n_keywords} Most Frequent Keywords',
            color='Frequency',
            color_continuous_scale='Teal'
        )
        fig_keywords.update_layout(height=600, showlegend=False)
        fig_keywords.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_keywords, use_container_width=True)
    
    with col2:
        # Table
        st.subheader("📋 Keyword Frequency Table")
        keywords_table = pd.DataFrame(top_keywords, columns=['Keyword', 'Frequency'])
        keywords_table['Rank'] = range(1, len(keywords_table) + 1)
        keywords_table = keywords_table[['Rank', 'Keyword', 'Frequency']]
        st.dataframe(
            keywords_table,
            hide_index=True,
            use_container_width=True,
            height=600
        )
    
    # Legal terms analysis
    st.markdown("---")
    st.subheader("⚖️ Common Legal Terms Analysis")
    
    legal_terms = [
        'agreement', 'party', 'parties', 'contract', 'terms', 'conditions',
        'liability', 'indemnity', 'termination', 'breach', 'confidential',
        'warranty', 'intellectual', 'property', 'arbitration', 'jurisdiction',
        'damages', 'obligation', 'rights', 'shall'
    ]
    
    legal_freq = [(term, dict(keywords).get(term, 0)) for term in legal_terms]
    legal_freq = sorted(legal_freq, key=lambda x: x[1], reverse=True)
    
    legal_df = pd.DataFrame(legal_freq, columns=['Legal Term', 'Frequency'])
    legal_df = legal_df[legal_df['Frequency'] > 0]
    
    fig_legal = px.bar(
        legal_df,
        x='Frequency',
        y='Legal Term',
        orientation='h',
        title='Common Legal Terms Frequency',
        color='Frequency',
        color_continuous_scale='Reds'
    )
    fig_legal.update_layout(height=400, showlegend=False)
    fig_legal.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_legal, use_container_width=True)

# TAB 4: Contract Explorer
with tab4:
    st.header("📄 Contract Explorer")
    
    # Select contract
    contract_options = df_filtered['filename'].tolist()
    selected_contract = st.selectbox("Select a contract to view:", contract_options)
    
    if selected_contract:
        contract_data = df_filtered[df_filtered['filename'] == selected_contract].iloc[0]
        
        # Contract info
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Word Count", f"{contract_data['word_count']:,}")
        with col2:
            st.metric("Character Count", f"{contract_data['char_count']:,}")
        with col3:
            st.metric("Line Count", f"{contract_data['line_count']:,}")
        with col4:
            st.metric("File Size", f"{contract_data['file_size_kb']:.2f} KB")
        
        st.markdown("---")
        
        # Show contract text
        st.subheader("Contract Content")
        
        # Preview options
        preview_length = st.slider("Preview length (characters)", 500, 5000, 1000, step=500)
        
        with st.expander("📖 View Contract Text", expanded=True):
            st.text_area(
                "Contract Content",
                value=contract_data['content'][:preview_length] + "\n\n... (truncated)",
                height=400,
                disabled=True
            )
        
        # Check if cleaned version exists
        cleaned_path = TRANSFORMED_DIR / f"{contract_data['contract_id']}_cleaned.txt"
        if cleaned_path.exists():
            st.success("✅ Cleaned version available")
            
            if st.button("Compare Original vs Cleaned"):
                with open(cleaned_path, 'r', encoding='utf-8') as f:
                    cleaned_content = f.read()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Original")
                    st.text_area("Original", contract_data['content'][:1000], height=300, disabled=True)
                with col2:
                    st.subheader("Cleaned")
                    st.text_area("Cleaned", cleaned_content[:1000], height=300, disabled=True)
                
                reduction = ((len(contract_data['content']) - len(cleaned_content)) / len(contract_data['content'])) * 100
                st.metric("Size Reduction", f"{reduction:.1f}%")

# TAB 5: Data Table
with tab5:
    st.header("📋 Complete Data Table")
    
    # Display options
    columns_to_show = st.multiselect(
        "Select columns to display:",
        options=['filename', 'word_count', 'char_count', 'line_count', 'file_size_kb'],
        default=['filename', 'word_count', 'file_size_kb']
    )
    
    if columns_to_show:
        # Sort options
        sort_by = st.selectbox("Sort by:", columns_to_show)
        sort_order = st.radio("Sort order:", ['Descending', 'Ascending'], horizontal=True)
        
        display_df = df_filtered[columns_to_show].copy()
        display_df = display_df.sort_values(
            by=sort_by, 
            ascending=(sort_order == 'Ascending')
        )
        
        st.dataframe(
            display_df,
            hide_index=True,
            use_container_width=True,
            height=500
        )
        
        # Download button
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name="contract_statistics.csv",
            mime="text/csv"
        )
    else:
        st.warning("Please select at least one column to display")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>Contract Analysis Dashboard | "
    "Built with Streamlit 🎈</div>",
    unsafe_allow_html=True
)
