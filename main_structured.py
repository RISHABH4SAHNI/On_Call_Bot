import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

sys.path.append(str(Path(__file__).parent))

from core.workflow_engine import WorkflowEngine
from factories.service_factory import ServiceFactory

def main():
    print("Code Analysis System - Restructured")
    print("=" * 50)
    print("1. Process Repository")
    print("2. Analyze Issue")
    print("3. Launch Streamlit UI")
    print("4. Export Function Lookup Table")
    print("5. View Analysis History")
    print("6. Export Analysis History")
    print("7. Exit")
    print()
    
    workflow_engine = None
    
    while True:
        try:
            choice = input("Choose an option (1-7): ").strip()
            
            # Validate services on first use
            if choice in ["1", "2"] and workflow_engine:
                print("Validating services...")
                validation = workflow_engine.validate_services()
                failed_services = [k for k, v in validation.items() if not v]
                if failed_services:
                    print(f"Warning: Some services failed validation: {failed_services}")
                    continue_anyway = input("Continue anyway? (y/n): ").lower()
                    if continue_anyway != 'y':
                        continue
            
            if choice == "1":
                print("\nRepository Processing")
                print("-" * 30)
                
                embedding_service = input("Embedding service (openai/ollama/perplexity) [openai]: ").strip() or "openai"
                repo_path = input("Repository path: ").strip()
                
                if not repo_path or not os.path.exists(repo_path):
                    print("Invalid repository path")
                    continue
                
                print(f"Processing repository with {embedding_service} embeddings...")
                
                try:
                    workflow_engine = WorkflowEngine(
                        embedding_service_type=embedding_service,
                        llm_service_type="openai"
                    )
                    
                    result = workflow_engine.process_repository(repo_path)
                except Exception as e:
                    print(f"Error processing repository: {e}")
                    print("Please check:")
                    print("- Repository path is correct")
                    print("- OpenSearch is running")
                    print("- API keys are configured")
                    continue
                
                print(f"Processing complete!")
                print(f"Total functions: {result['total_functions']}")
                print(f"Embedded functions: {result['embedded_functions']}")
                print(f"Success rate: {(result['embedded_functions']/result['total_functions']*100):.1f}%")
                print()
                
            elif choice == "2":
                if not workflow_engine:
                    print("Please process a repository first (option 1)")
                    continue
                
                print("\nIssue Analysis")
                print("-" * 30)
                
                llm_service = input("LLM service (openai/perplexity/ollama) [openai]: ").strip() or "openai"
                
                workflow_engine = WorkflowEngine(
                    embedding_service_type=workflow_engine.embedding_service_type,
                    llm_service_type=llm_service
                )
                
                user_query = input("Describe your issue: ").strip()
                if not user_query:
                    print("No query provided")
                    continue
                
                context = {}
                repo_name = input("Repository name (optional): ").strip()
                if repo_name:
                    context["repo_name"] = repo_name
                
                print(f"Analyzing with {llm_service}...")
                
                try:
                    result = workflow_engine.analyze_user_issue(user_query, context)
                except Exception as e:
                    print(f"Error during analysis: {e}")
                    continue
                
                if "error" in result:
                    print(f"Error: {result['error']}")
                else:
                    print(f"\nAnalysis Results:")
                    print(f"Enhanced Query: {result['enhanced_query']}")
                    print(f"Functions Found: {result['functions_found']}")
                    print(f"Confidence Score: {result['confidence_score']:.2f}")
                    print(f"\nAnalysis:")
                    print("-" * 50)
                    print(result['analysis'])
                    print("-" * 50)
                print()
                
            elif choice == "3":
                print("Launching Streamlit UI...")
                import subprocess
                try:
                    subprocess.run([
                        sys.executable, "-m", "streamlit", "run", 
                        str(Path(__file__).parent / "ui" / "streamlit_app.py")
                    ])
                except KeyboardInterrupt:
                    print("Streamlit UI closed")
                
            elif choice == "4":
                if not workflow_engine:
                    print("Please process a repository first (option 1)")
                    continue
                
                export_format = input("Export format (csv/json) [json]: ").strip().lower() or "json"
                
                try:
                    if export_format == "json":
                        output_file = input("Output JSON file path [function_lookup.json]: ").strip() or "function_lookup.json"
                        workflow_engine.export_function_lookup_table(output_file, "json")
                    else:
                        output_file = input("Output CSV file path [function_lookup.csv]: ").strip() or "function_lookup.csv"
                        workflow_engine.export_function_lookup_table(output_file, "csv")
                    
                    print(f"Function lookup table exported to {output_file}")
                except Exception as e:
                    print(f"Error exporting lookup table: {e}")
                
                print()
                
            elif choice == "5":
                if not workflow_engine:
                    print("No analysis history available")
                    continue
                
                history_stats = workflow_engine.get_analysis_history_stats()
                recent_analyses = workflow_engine.get_recent_analyses(5)
                
                print("\nAnalysis History Statistics:")
                print(f"Total analyses: {history_stats['total_analyses']}")
                print(f"Average confidence: {history_stats['average_confidence']}")
                print(f"Services usage: {history_stats.get('services_usage', {})}")
                
                print("\nRecent Analyses:")
                for analysis in recent_analyses:
                    print(f"- {analysis['timestamp']}: {analysis['query'][:50]}... (Confidence: {analysis['confidence_score']})")
                print()
                
            elif choice == "6":
                if not workflow_engine:
                    print("No analysis history available")
                    continue
                
                output_file = input("Output history file [analysis_history_export.json]: ").strip() or "analysis_history_export.json"
                
                try:
                    workflow_engine.history_manager.export_history(output_file)
                    print(f"Analysis history exported to {output_file}")
                except Exception as e:
                    print(f"Error exporting history: {e}")
                print()
                
            elif choice == "7":
                print("Goodbye!")
                break
                
            else:
                print("Invalid choice. Please enter 1-7.")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

def run_streamlit():
    import streamlit.web.cli as stcli
    import sys
    sys.argv = ["streamlit", "run", str(Path(__file__).parent / "ui" / "streamlit_app.py")]
    stcli.main()

if __name__ == "__main__":
    main()
