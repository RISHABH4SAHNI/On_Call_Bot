import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from core.workflow_engine import WorkflowEngine
from factories.service_factory import ServiceFactory
from config.settings import SUPPORTED_APPROACHES, DEFAULT_ANALYSIS_APPROACH
from utils.helpers import validate_repository_path, clean_error_message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CodeAnalysisSystem:
    def __init__(self):
        self.workflow_engine: Optional[WorkflowEngine] = None
        self.current_approach = DEFAULT_ANALYSIS_APPROACH
        self.service_factory = ServiceFactory()
        
    def display_banner(self):
        """Display system banner"""
        print("╔" + "═" * 58 + "╗")
        print("║" + " " * 10 + "Code Analysis System - Restructured" + " " * 11 + "║")
        print("╠" + "═" * 58 + "╣")
        print("║  1. Process Repository                                 ║")
        print("║  2. Analyze Issue                                      ║") 
        print("║  3. Launch Streamlit UI                                ║")
        print("║  4. Export Function Lookup Table                      ║")
        print("║  5. Switch Analysis Approach                           ║")
        print("║  6. View Analysis History                              ║")
        print("║  7. Export Analysis History                            ║")
        print("║  8. System Diagnostics                                 ║")
        print("║  9. Clear Analysis History                             ║") 
        print("║  0. Exit                                               ║")
        print("╚" + "═" * 58 + "╝")
        print()

    def display_status(self):
        """Display current system status"""
        print(f"📊 Current Analysis Approach: {self.current_approach}")
        print(f"🔧 Available Approaches: {', '.join(SUPPORTED_APPROACHES)}")
        print(f"⚙️  Workflow Engine: {'✅ Initialized' if self.workflow_engine else '❌ Not initialized'}")
        if self.workflow_engine:
            stats = self.get_quick_stats()
            print(f"📈 Total Analyses: {stats.get('total_analyses', 0)}")
        print()

    def get_quick_stats(self) -> Dict[str, Any]:
        """Get quick system statistics"""
        try:
            if self.workflow_engine:
                return self.workflow_engine.get_analysis_history_stats()
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
        return {}

    def validate_services(self, embedding_service: str, llm_service: str) -> bool:
        """Validate if services are properly configured"""
        try:
            # Check if required environment variables are set
            if embedding_service == "openai" and not os.getenv('OPENAI_API_KEY'):
                print("❌ OpenAI API key not found in environment variables")
                return False
            if embedding_service == "perplexity" and not os.getenv('PERPLEXITY_API_KEY'):
                print("❌ Perplexity API key not found in environment variables")
                return False
            return True
        except Exception as e:
            logger.error(f"Service validation failed: {e}")
            return False

    def process_repository(self):
        """Handle repository processing with comprehensive error handling"""
        print("\n" + "="*60)
        print("🏗️  REPOSITORY PROCESSING")
        print("="*60)
        
        try:
            # Get analysis approach
            print(f"Available approaches: {', '.join(SUPPORTED_APPROACHES)}")
            approach_choice = input(f"Analysis approach [{self.current_approach}]: ").strip()
            if approach_choice and approach_choice in SUPPORTED_APPROACHES:
                self.current_approach = approach_choice
            elif approach_choice and approach_choice not in SUPPORTED_APPROACHES:
                print(f"❌ Invalid approach '{approach_choice}'. Using {self.current_approach}")

            # Get service preferences
            embedding_service = input("Embedding service (openai/ollama/perplexity) [openai]: ").strip() or "openai"
            llm_service = input("LLM service (openai/perplexity/ollama) [openai]: ").strip() or "openai"
            
            # Validate services
            if not self.validate_services(embedding_service, llm_service):
                print("❌ Service validation failed. Please check your configuration.")
                return

            # Get repository path with validation
            repo_path = input("Repository path: ").strip()
            if not repo_path:
                print("❌ Repository path cannot be empty")
                return
                
            repo_path = os.path.abspath(repo_path)
            if not validate_repository_path(repo_path):
                print("❌ Invalid repository path or no Python files found")
                print("💡 Ensure the path contains Python (.py) files")
                return

            # Additional options
            include_tests = input("Include test files? (y/n) [n]: ").strip().lower() == 'y'
            
            print(f"\n🚀 Processing repository...")
            print(f"   📁 Path: {repo_path}")
            print(f"   🔧 Approach: {self.current_approach}")
            print(f"   🤖 Embedding: {embedding_service}")
            print(f"   🧠 LLM: {llm_service}")
            print(f"   🧪 Include tests: {include_tests}")
            print()

            # Initialize workflow engine
            try:
                self.workflow_engine = WorkflowEngine(
                    embedding_service_type=embedding_service,
                    llm_service_type=llm_service,
                    analysis_approach=self.current_approach
                )
                
                # Validate services
                validation = self.workflow_engine.validate_services()
                failed_services = [k for k, v in validation.items() if not v]
                
                if failed_services:
                    print(f"⚠️  Some services failed validation: {failed_services}")
                    print("💡 Check your API keys and service configurations")
                    if not input("Continue anyway? (y/n) [n]: ").strip().lower() == 'y':
                        return
                else:
                    print("✅ All services validated successfully!")
                    
            except Exception as e:
                print(f"❌ Failed to initialize workflow engine: {clean_error_message(str(e))}")
                self.display_troubleshooting_info()
                return

            # Process repository
            try:
                print("⏳ Processing repository... This may take a few minutes.")
                result = self.workflow_engine.process_repository(repo_path)
                
                print("\n✅ Processing complete!")
                print(f"📊 Results:")
                print(f"   📝 Total functions: {result.get('total_functions', 0)}")
                print(f"   💾 Embedded functions: {result.get('embedded_functions', 0)}")
                print(f"   🎯 Approach: {result.get('approach', self.current_approach)}")
                
                total = result.get('total_functions', 0)
                embedded = result.get('embedded_functions', 0)
                if total > 0:
                    success_rate = (embedded / total) * 100
                    print(f"   ✨ Success rate: {success_rate:.1f}%")
                    
                    if success_rate < 80:
                        print("⚠️  Low success rate detected. Check:")
                        print("   • OpenSearch connectivity")
                        print("   • API key validity")
                        print("   • Network connectivity")

                if "summary" in result:
                    summary = result["summary"]
                    print(f"\n📈 Repository Summary:")
                    print(f"   ⚡ Async functions: {summary.get('async_functions', 0)}")
                    print(f"   🛡️  With error handling: {summary.get('functions_with_error_handling', 0)}")
                    print(f"   📦 Unique modules: {summary.get('unique_modules', 0)}")
                    
            except Exception as e:
                print(f"❌ Repository processing failed: {clean_error_message(str(e))}")
                self.display_troubleshooting_info()
                
        except KeyboardInterrupt:
            print("\n⏹️  Processing cancelled by user")
        except Exception as e:
            logger.error(f"Repository processing error: {e}")
            print(f"❌ Unexpected error: {clean_error_message(str(e))}")

    def analyze_issue(self):
        """Handle issue analysis with enhanced error handling"""
        if not self.workflow_engine:
            print("❌ Please process a repository first (option 1)")
            return

        print("\n" + "="*60)
        print("🔍 ISSUE ANALYSIS")
        print("="*60)
        
        try:
            # Get LLM service preference
            llm_service = input("LLM service (openai/perplexity/ollama) [current]: ").strip()
            if llm_service and llm_service in ["openai", "perplexity", "ollama"]:
                try:
                    # Update LLM service
                    self.workflow_engine.analysis_service = self.service_factory.get_analysis_service(llm_service)
                    self.workflow_engine.query_enhancer = self.service_factory.get_query_enhancer(llm_service)
                    print(f"✅ Updated LLM service to {llm_service}")
                except Exception as e:
                    print(f"⚠️  Failed to update LLM service: {e}")

            # Get user query
            print("\n🤔 Describe your issue:")
            user_query = input("Query: ").strip()
            if not user_query:
                print("❌ No query provided")
                return
                
            if len(user_query) > 1000:
                print("⚠️  Query is very long. Truncating to 1000 characters.")
                user_query = user_query[:1000]

            # Collect additional context
            context = {}
            print("\n📝 Additional context (optional):")
            
            repo_name = input("Repository name: ").strip()
            if repo_name:
                context["repo_name"] = repo_name
                
            tech_stack = input("Tech stack (comma-separated): ").strip()
            if tech_stack:
                context["tech_stack"] = [t.strip() for t in tech_stack.split(",")]
                
            priority = input("Priority (low/medium/high/critical): ").strip().lower()
            if priority in ["low", "medium", "high", "critical"]:
                context["priority"] = priority

            # Approach-specific context
            if self.workflow_engine.analysis_approach == "call_graph":
                depth_input = input("Call graph depth (1-5) [3]: ").strip()
                if depth_input and depth_input.isdigit():
                    depth = int(depth_input)
                    if 1 <= depth <= 5:
                        context["call_graph_depth"] = depth

            print(f"\n🧠 Analyzing with approach: {self.workflow_engine.analysis_approach}")
            print("⏳ This may take a minute...")
            
            try:
                result = self.workflow_engine.analyze_user_issue(user_query, context)
                
                if "error" in result:
                    print(f"❌ Analysis failed: {result['error']}")
                    return

                print("\n" + "="*60)
                print("📊 ANALYSIS RESULTS")
                print("="*60)
                
                print(f"🔍 Original Query: {user_query}")
                print(f"✨ Enhanced Query: {result.get('enhanced_query', 'N/A')}")
                print(f"📝 Functions Found: {result.get('functions_found', 0)}")
                print(f"📈 Functions Analyzed: {result.get('functions_analyzed', 0)}")
                print(f"🎯 Confidence Score: {result.get('confidence_score', 0):.2f}")
                print(f"🔧 Approach Used: {result.get('approach', 'unknown')}")
                
                confidence = result.get('confidence_score', 0)
                if confidence >= 0.8:
                    print("🟢 High confidence result")
                elif confidence >= 0.6:
                    print("🟡 Medium confidence result")
                else:
                    print("🔴 Low confidence result - consider refining your query")

                print(f"\n🤖 AI ANALYSIS:")
                print("-" * 60)
                analysis_text = result.get('analysis', 'No analysis available')
                print(analysis_text)
                print("-" * 60)
                
                # Display function details if available
                if result.get('search_results'):
                    print(f"\n📋 RELEVANT FUNCTIONS ({len(result['search_results'])}):")
                    for i, search_result in enumerate(result['search_results'][:3], 1):  # Show top 3
                        func = search_result.function_metadata
                        print(f"{i}. {func.name} (Score: {search_result.relevance_score:.3f})")
                        print(f"   📁 File: {func.file_path}")
                        print(f"   📍 Lines: {func.start_line}-{func.end_line}")
                        if func.class_context:
                            print(f"   🏷️  Class: {func.class_context}")
                        
            except Exception as e:
                print(f"❌ Analysis failed: {clean_error_message(str(e))}")
                logger.error(f"Analysis error: {e}")
                
        except KeyboardInterrupt:
            print("\n⏹️  Analysis cancelled by user")
        except Exception as e:
            logger.error(f"Issue analysis error: {e}")
            print(f"❌ Unexpected error: {clean_error_message(str(e))}")

    def launch_streamlit_ui(self):
        """Launch Streamlit UI with proper error handling"""
        print("\n🚀 Launching Streamlit UI...")
        
        ui_path = Path(__file__).parent / "ui" / "streamlit_app.py"
        if not ui_path.exists():
            print(f"❌ Streamlit app not found at {ui_path}")
            return
            
        try:
            import subprocess
            print("🌐 Opening browser... Press Ctrl+C to stop the server")
            subprocess.run([
                sys.executable, "-m", "streamlit", "run", 
                str(ui_path),
                "--server.address", "localhost",
                "--server.port", "8501",
                "--browser.gatherUsageStats", "false"
            ])
        except KeyboardInterrupt:
            print("\n⏹️  Streamlit UI closed")
        except FileNotFoundError:
            print("❌ Streamlit not installed. Run: pip install streamlit")
        except Exception as e:
            print(f"❌ Failed to launch Streamlit: {clean_error_message(str(e))}")

    def export_function_lookup_table(self):
        """Export function lookup table with validation"""
        if not self.workflow_engine:
            print("❌ Please process a repository first (option 1)")
            return

        print("\n" + "="*60)
        print("💾 EXPORT FUNCTION LOOKUP TABLE")
        print("="*60)
        
        try:
            export_format = input("Export format (csv/json) [json]: ").strip().lower() or "json"
            if export_format not in ["csv", "json"]:
                print("❌ Invalid format. Using JSON.")
                export_format = "json"
                
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_name = f"function_lookup_{timestamp}.{export_format}"
            output_file = input(f"Output file [{default_name}]: ").strip() or default_name
            
            print(f"📊 Exporting function lookup table...")
            self.workflow_engine.export_function_lookup_table(output_file, export_format)
            
            # Verify file was created
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"✅ Export successful!")
                print(f"   📁 File: {output_file}")
                print(f"   📏 Size: {file_size:,} bytes")
            else:
                print("❌ Export failed - file not created")
                
        except Exception as e:
            print(f"❌ Export failed: {clean_error_message(str(e))}")
            logger.error(f"Export error: {e}")

    def switch_analysis_approach(self):
        """Switch analysis approach with proper validation"""
        if not self.workflow_engine:
            print("❌ Please initialize workflow engine first (option 1)")
            return

        print("\n" + "="*60)
        print("🔄 SWITCH ANALYSIS APPROACH")
        print("="*60)
        
        print(f"Current approach: {self.workflow_engine.analysis_approach}")
        print("\nAvailable approaches:")
        
        approaches = self.service_factory.get_supported_approaches()
        for i, approach in enumerate(approaches, 1):
            current = " (current)" if approach['key'] == self.workflow_engine.analysis_approach else ""
            print(f"{i}. {approach['name']}{current}")
            print(f"   {approach['description']}")
            
        try:
            choice = input(f"\nSelect new approach ({'/'.join(SUPPORTED_APPROACHES)}): ").strip()
            if choice in SUPPORTED_APPROACHES and choice != self.workflow_engine.analysis_approach:
                print(f"🔄 Switching to {choice} approach...")
                self.workflow_engine.switch_analysis_approach(choice)
                self.current_approach = choice
                print(f"✅ Successfully switched to {choice} approach")
            elif choice == self.workflow_engine.analysis_approach:
                print("ℹ️  Already using that approach")
            else:
                print("❌ Invalid approach selected")
                
        except Exception as e:
            print(f"❌ Failed to switch approach: {clean_error_message(str(e))}")
            logger.error(f"Switch approach error: {e}")

    def view_analysis_history(self):
        """View analysis history with detailed statistics"""
        if not self.workflow_engine:
            print("❌ No analysis history available")
            return

        print("\n" + "="*60)
        print("📈 ANALYSIS HISTORY")
        print("="*60)
        
        try:
            history_stats = self.workflow_engine.get_analysis_history_stats()
            recent_analyses = self.workflow_engine.get_recent_analyses(10)
            
            print("📊 Statistics:")
            print(f"   📝 Total analyses: {history_stats.get('total_analyses', 0)}")
            print(f"   🎯 Average confidence: {history_stats.get('average_confidence', 0):.3f}")
            
            services_usage = history_stats.get('services_usage', {})
            if services_usage:
                print(f"   🔧 Services usage:")
                for service_combo, count in services_usage.items():
                    print(f"      • {service_combo}: {count}")
            
            created_at = history_stats.get('created_at')
            if created_at:
                print(f"   📅 History created: {created_at[:19]}")
                
            file_size = history_stats.get('file_size_mb', 0)
            print(f"   💾 History file size: {file_size:.2f} MB")
            
            print(f"\n📋 Recent Analyses ({len(recent_analyses)}):")
            if recent_analyses:
                for i, analysis in enumerate(recent_analyses, 1):
                    timestamp = analysis['timestamp'][:19]
                    query = analysis['query'][:50] + "..." if len(analysis['query']) > 50 else analysis['query']
                    confidence = analysis.get('confidence_score', 0)
                    print(f"{i:2d}. {timestamp} | {query} | {confidence:.2f}")
            else:
                print("   No analyses found")
                
        except Exception as e:
            print(f"❌ Failed to retrieve history: {clean_error_message(str(e))}")
            logger.error(f"View history error: {e}")

    def export_analysis_history(self):
        """Export analysis history to file"""
        if not self.workflow_engine:
            print("❌ No analysis history available")
            return

        print("\n" + "="*60)
        print("💾 EXPORT ANALYSIS HISTORY")
        print("="*60)
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_name = f"analysis_history_export_{timestamp}.json"
            output_file = input(f"Output file [{default_name}]: ").strip() or default_name
            
            print("📊 Exporting analysis history...")
            self.workflow_engine.history_manager.export_history(output_file)
            
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"✅ Export successful!")
                print(f"   📁 File: {output_file}")
                print(f"   📏 Size: {file_size:,} bytes")
            else:
                print("❌ Export failed - file not created")
                
        except Exception as e:
            print(f"❌ Export failed: {clean_error_message(str(e))}")
            logger.error(f"Export history error: {e}")

    def system_diagnostics(self):
        """Run system diagnostics"""
        print("\n" + "="*60)
        print("🔧 SYSTEM DIAGNOSTICS")
        print("="*60)
        
        # Check Python version
        print(f"🐍 Python version: {sys.version}")
        
        # Check required packages
        required_packages = ['openai', 'opensearchpy', 'streamlit', 'pandas', 'requests']
        print("\n📦 Package status:")
        for package in required_packages:
            try:
                __import__(package)
                print(f"   ✅ {package}")
            except ImportError:
                print(f"   ❌ {package} - not installed")
        
        # Check environment variables
        print("\n🔑 Environment variables:")
        env_vars = ['OPENAI_API_KEY', 'PERPLEXITY_API_KEY', 'OPENSEARCH_HOST']
        for var in env_vars:
            value = os.getenv(var)
            if value:
                masked_value = value[:8] + "*" * (len(value) - 8) if len(value) > 8 else "*" * len(value)
                print(f"   ✅ {var}: {masked_value}")
            else:
                print(f"   ❌ {var}: not set")
        
        # Check OpenSearch connectivity
        print("\n🔍 OpenSearch connectivity:")
        try:
            from opensearchpy import OpenSearch
            from config.settings import get_opensearch_config
            
            config = get_opensearch_config()
            client = OpenSearch(
                config['hosts'],
                http_auth=config['http_auth'],
                use_ssl=config['use_ssl'],
                timeout=5
            )
            info = client.info()
            print(f"   ✅ Connected to OpenSearch {info['version']['number']}")
        except Exception as e:
            print(f"   ❌ OpenSearch connection failed: {e}")
        
        # Workflow engine status
        if self.workflow_engine:
            print("\n⚙️  Workflow engine:")
            print(f"   ✅ Initialized")
            print(f"   🔧 Approach: {self.workflow_engine.analysis_approach}")
            
            try:
                validation = self.workflow_engine.validate_services()
                for service, status in validation.items():
                    icon = "✅" if status else "❌"
                    print(f"   {icon} {service}")
            except Exception as e:
                print(f"   ❌ Service validation failed: {e}")
        else:
            print("\n⚙️  Workflow engine: ❌ Not initialized")

    def clear_analysis_history(self):
        """Clear analysis history with confirmation"""
        if not self.workflow_engine:
            print("❌ No analysis history to clear")
            return
            
        print("\n⚠️  WARNING: This will permanently delete all analysis history!")
        confirm = input("Are you sure? Type 'yes' to confirm: ").strip().lower()
        
        if confirm == 'yes':
            try:
                self.workflow_engine.history_manager.clear_history()
                print("✅ Analysis history cleared successfully")
            except Exception as e:
                print(f"❌ Failed to clear history: {clean_error_message(str(e))}")
        else:
            print("❌ Operation cancelled")

    def display_troubleshooting_info(self):
        """Display troubleshooting information"""
        print("\n🔧 TROUBLESHOOTING:")
        print("• Ensure repository path is correct and contains Python files")
        print("• Check that OpenSearch is running on localhost:9200")
        print("• Verify API keys are properly configured in .env file")
        print("• Ensure network connectivity for external services")
        print("• Check Python package dependencies are installed")
        print("• Review error logs for detailed information")

    def run(self):
        """Main application loop"""
        try:
            while True:
                self.display_banner()
                self.display_status()
                
                try:
                    choice = input("Choose an option (0-9): ").strip()
                    
                    if choice == "1":
                        self.process_repository()
                    elif choice == "2":
                        self.analyze_issue()
                    elif choice == "3":
                        self.launch_streamlit_ui()
                    elif choice == "4":
                        self.export_function_lookup_table()
                    elif choice == "5":
                        self.switch_analysis_approach()
                    elif choice == "6":
                        self.view_analysis_history()
                    elif choice == "7":
                        self.export_analysis_history()
                    elif choice == "8":
                        self.system_diagnostics()
                    elif choice == "9":
                        self.clear_analysis_history()
                    elif choice == "0":
                        print("👋 Goodbye!")
                        break
                    else:
                        print("❌ Invalid choice. Please enter 0-9.")
                        
                    if choice != "0":
                        input("\nPress Enter to continue...")
                        
                except KeyboardInterrupt:
                    print("\n\n👋 Goodbye!")
                    break
                    
        except Exception as e:
            logger.error(f"Application error: {e}")
            print(f"❌ Application error: {clean_error_message(str(e))}")

def main():
    """Main entry point for the Code Analysis System"""
    try:
        # Load environment variables if available
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Environment variables loaded")
    except ImportError:
        logger.warning("python-dotenv not installed, skipping .env file loading")
    except Exception as e:
        logger.warning(f"Could not load .env file: {e}")
    
    try:
        # Initialize and run the Code Analysis System
        system = CodeAnalysisSystem()
        logger.info("Code Analysis System initialized successfully")
        system.run()
    except KeyboardInterrupt:
        print("\n\n👋 Application interrupted by user")
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        print(f"❌ Fatal error: {clean_error_message(str(e))}")
        print("\n🔧 For troubleshooting help, run option 8 (System Diagnostics) or check the logs.")
        print("📋 Common issues:")
        print("  - Check .env file exists with required API keys")
        print("  - Ensure OpenSearch is running if using vector search")
        print("  - Verify Python dependencies are installed")
        return 1
    
    return 0


def run_streamlit():
    """Run the Streamlit UI directly"""
    import subprocess
    import sys
    ui_path = Path(__file__).parent / "ui" / "streamlit_app.py"
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        str(ui_path)
    ])



if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


