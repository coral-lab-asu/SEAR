#!/usr/bin/env python3
"""
Meta Prompting Error Analysis Script

This script performs comprehensive error analysis on meta prompting failures
across multiple QA datasets (fetaqa, finqa, hitabs, hybridqa, sqa, squall, tatqa, wiki).

Author: Expert Python Developer
Usage: python error_analysis.py --dataset fetaqa --api_provider gemini --output_dir ./analysis_results
"""

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import time
import re

import pymongo
from pymongo import MongoClient
import google.generativeai as genai
import openai
from tqdm import tqdm
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('error_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class EnvironmentConfig:
    """Handles environment configuration and validation"""
    
    def __init__(self):
        self.mongo_connection = self._get_env_var('MONGO_CONNECTION_STRING', 'mongodb://localhost:27017/')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # Validate configuration
        self._validate_config()
    
    def _get_env_var(self, key: str, default: str = None) -> str:
        """Get environment variable with optional default"""
        value = os.getenv(key, default)
        if value is None:
            raise ValueError(f"Environment variable {key} is required but not set")
        return value
    
    def _validate_config(self):
        """Validate that required environment variables are set"""
        if not self.gemini_api_key and not self.openai_api_key:
            raise ValueError("Either GEMINI_API_KEY or OPENAI_API_KEY must be set in environment")
        
        logger.info("Environment configuration loaded successfully")
        logger.info(f"MongoDB: {self.mongo_connection}")
        logger.info(f"Gemini API: {'Available' if self.gemini_api_key else 'Not configured'}")
        logger.info(f"OpenAI API: {'Available' if self.openai_api_key else 'Not configured'}")
    
    def get_api_key(self, provider: str) -> str:
        """Get API key for specified provider"""
        if provider.lower() == 'gemini':
            if not self.gemini_api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            return self.gemini_api_key
        elif provider.lower() == 'openai':
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY not found in environment variables")
            return self.openai_api_key
        else:
            raise ValueError(f"Unsupported API provider: {provider}")


@dataclass
class ErrorCase:
    """Data class to represent an error case"""
    _id: str
    dataset: str
    question: str
    answer: str
    response: str
    extracted_response: str
    code_output: str
    f1_final: float
    f1_score_extracted_response: float
    f1_score_code_output: float
    reasoning_type: str
    model: str
    q_num: int


@dataclass
class ErrorAnalysis:
    """Data class to represent error analysis results"""
    case_id: str
    dataset: str
    error_category: str
    failure_reason: str
    detailed_analysis: str
    suggested_improvement: str
    confidence_score: float


class DatabaseConnector:
    """Handles MongoDB connections and queries"""
    
    def __init__(self, config: EnvironmentConfig):
        self.config = config
        self.client = None
        self.db = None
    
    def connect(self):
        """Establish database connection using environment config"""
        try:
            # Configure connection with appropriate timeouts for Atlas
            self.client = MongoClient(
                self.config.mongo_connection,
                serverSelectionTimeoutMS=30000,  # 30 seconds
                connectTimeoutMS=30000,
                socketTimeoutMS=30000,
                maxPoolSize=10,
                retryWrites=True
            )
            
            # Test connection
            self.client.server_info()
            logger.info(f"Successfully connected to MongoDB Atlas cluster")
            
            # List available databases for verification
            databases = self.client.list_database_names()
            logger.info(f"Available databases: {databases}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB Atlas: {e}")
            logger.error("Please check your MongoDB Atlas connection string and ensure:")
            logger.error("1. Your IP address is whitelisted in Atlas")
            logger.error("2. Your username/password are correct")
            logger.error("3. Your cluster is running")
            raise
    
    def get_error_cases(self, dataset: str, f1_threshold: float = 80.0) -> List[Dict]:
        """
        Fetch error cases from the specified dataset
        
        Args:
            dataset: Name of the dataset (will be used as database name)
            f1_threshold: F1 score threshold below which cases are considered errors
            
        Returns:
            List of error cases
        """
        try:
            # Use dataset name as database name and look in 'meta' collection
            db = self.client[dataset]  # dataset is the database name
            collection = db['meta']    # 'meta' appears to be the collection with evaluation results
            
            query = {
                "$and": [
                    {
                        "gem_eval_extracted_response": {
                            "$regex": "^No",
                            "$options": "i"
                        }
                    },
                    {
                        "f1_final": {"$lt": f1_threshold}
                    }
                ]
            }
            
            cursor = collection.find(query)
            cases = list(cursor)
            logger.info(f"Found {len(cases)} error cases in {dataset} database, meta collection")
            
            return cases
            
        except Exception as e:
            logger.error(f"Error fetching data from {dataset} database: {e}")
            logger.info("Available collections in this database:")
            try:
                db = self.client[dataset]
                collections = db.list_collection_names()
                logger.info(f"Collections: {collections}")
            except:
                pass
            return []
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")


class LLMAnalyzer:
    """Handles LLM-based error analysis"""
    
    def __init__(self, api_provider: str, config: EnvironmentConfig):
        self.api_provider = api_provider.lower()
        self.config = config
        self.api_key = config.get_api_key(api_provider)
        self._setup_client()
    
    def _setup_client(self):
        """Initialize the appropriate LLM client"""
        if self.api_provider == "gemini":
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
            logger.info("Initialized Gemini client")
        elif self.api_provider == "openai":
            openai.api_key = self.api_key
            self.model_name = "gpt-4-turbo-preview"
            logger.info("Initialized OpenAI client")
        else:
            raise ValueError(f"Unsupported API provider: {self.api_provider}")
    
    def analyze_error_case(self, error_case: ErrorCase) -> ErrorAnalysis:
        """
        Perform detailed error analysis on a single case
        
        Args:
            error_case: The error case to analyze
            
        Returns:
            ErrorAnalysis object with detailed analysis
        """
        prompt = self._create_analysis_prompt(error_case)
        
        try:
            if self.api_provider == "gemini":
                response = self._query_gemini(prompt)
            else:
                response = self._query_openai(prompt)
            
            return self._parse_analysis_response(response, error_case)
            
        except Exception as e:
            logger.error(f"Error analyzing case {error_case._id}: {e}")
            return self._create_fallback_analysis(error_case, str(e))
    
    def _create_analysis_prompt(self, error_case: ErrorCase) -> str:
        """Create a comprehensive analysis prompt"""
        prompt = f"""
You are an expert in natural language processing and meta-reasoning systems for question-answering. 
Analyze the following failed meta prompting case where the system was unable to extract a proper answer 
(gem_eval_extracted_response = No) and achieved a low F1 score ({error_case.f1_final:.2f}).

**CONTEXT: Meta-Reasoning Framework**
The system uses a structured meta-reasoning approach with these components:
1. **Problem Understanding**: Determine objective, understand problem scope
2. **Reasoning Process**: Step-by-step reasoning, information extraction, decomposition into sub-problems
3. **Answer Formation**: Summarize findings, provide "Final Answer: [Answer]" format

**ERROR CASE DETAILS:**
**Dataset**: {error_case.dataset}
**Question**: {error_case.question}
**Expected Answer**: {error_case.answer}
**Model Response**: {error_case.response}
**Extracted Response**: {error_case.extracted_response}
**Code Output**: {error_case.code_output}
**F1 Score (Final)**: {error_case.f1_final}
**F1 Score (Extracted Response)**: {error_case.f1_score_extracted_response}
**F1 Score (Code Output)**: {error_case.f1_score_code_output}
**Reasoning Type**: {error_case.reasoning_type}

**ANALYSIS TASK:**
The evaluation system marked gem_eval_extracted_response as "No", meaning it failed to properly extract 
the final answer from the model's response, despite the model potentially providing correct reasoning.

Please provide a comprehensive analysis following this structure:

1. **ERROR_CATEGORY**: Choose the most appropriate category:
   - answer_format_failure: Model didn't use proper "Final Answer: [Answer]" format
   - reasoning_incomplete: Started reasoning but didn't complete the process
   - extraction_parsing_error: Answer present but extraction system failed to parse it
   - meta_structure_violation: Didn't follow the required meta-reasoning structure
   - content_accuracy_low: Followed format but provided incorrect information
   - code_execution_failure: Python code failed to execute or produce results
   - response_truncation: Response was cut off or incomplete

2. **FAILURE_REASON**: One-sentence summary of the primary failure cause

3. **DETAILED_ANALYSIS**: Comprehensive analysis (4-6 sentences) explaining:
   - What specific aspect of the meta-reasoning framework failed
   - Whether the reasoning process was correct but extraction failed
   - How the response format deviated from expected structure
   - Why the gem_eval system marked this as "No"

4. **SUGGESTED_IMPROVEMENT**: Specific recommendations for fixing this type of error:
   - Prompt engineering improvements
   - Format enforcement strategies
   - Validation mechanisms

5. **CONFIDENCE_SCORE**: Your confidence in this analysis (0.0-1.0)

Format your response as:
ERROR_CATEGORY: [category]
FAILURE_REASON: [reason]
DETAILED_ANALYSIS: [analysis]
SUGGESTED_IMPROVEMENT: [improvement]
CONFIDENCE_SCORE: [score]
"""
        return prompt
    
    def _query_gemini(self, prompt: str) -> str:
        """Query Gemini API"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            time.sleep(2)  # Rate limiting
            raise
    
    def _query_openai(self, prompt: str) -> str:
        """Query OpenAI API"""
        try:
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            time.sleep(2)  # Rate limiting
            raise
    
    def _parse_analysis_response(self, response: str, error_case: ErrorCase) -> ErrorAnalysis:
        """Parse the LLM analysis response"""
        try:
            # Extract structured information using regex
            error_category = re.search(r'ERROR_CATEGORY:\s*(.+)', response, re.IGNORECASE)
            failure_reason = re.search(r'FAILURE_REASON:\s*(.+)', response, re.IGNORECASE)
            detailed_analysis = re.search(r'DETAILED_ANALYSIS:\s*(.+?)(?=SUGGESTED_IMPROVEMENT|$)', response, re.IGNORECASE | re.DOTALL)
            suggested_improvement = re.search(r'SUGGESTED_IMPROVEMENT:\s*(.+?)(?=CONFIDENCE_SCORE|$)', response, re.IGNORECASE | re.DOTALL)
            confidence_score = re.search(r'CONFIDENCE_SCORE:\s*([0-9]*\.?[0-9]+)', response, re.IGNORECASE)
            
            return ErrorAnalysis(
                case_id=error_case._id,
                dataset=error_case.dataset,
                error_category=error_category.group(1).strip() if error_category else "unknown",
                failure_reason=failure_reason.group(1).strip() if failure_reason else "Unable to determine",
                detailed_analysis=detailed_analysis.group(1).strip() if detailed_analysis else response,
                suggested_improvement=suggested_improvement.group(1).strip() if suggested_improvement else "No specific improvement identified",
                confidence_score=float(confidence_score.group(1)) if confidence_score else 0.5
            )
        except Exception as e:
            logger.error(f"Error parsing analysis response: {e}")
            return self._create_fallback_analysis(error_case, response)
    
    def _create_fallback_analysis(self, error_case: ErrorCase, error_msg: str) -> ErrorAnalysis:
        """Create a fallback analysis when parsing fails"""
        return ErrorAnalysis(
            case_id=error_case._id,
            dataset=error_case.dataset,
            error_category="parsing_error",
            failure_reason=f"Analysis parsing failed: {error_msg}",
            detailed_analysis="Unable to perform detailed analysis due to parsing error",
            suggested_improvement="Review analysis prompt and response format",
            confidence_score=0.0
        )


class ErrorAnalysisReporter:
    """Generates comprehensive error analysis reports"""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_comprehensive_report(self, analyses: List[ErrorAnalysis], dataset: str) -> str:
        """Generate a comprehensive analysis report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"{dataset}_error_analysis_{timestamp}.txt"
        
        # Aggregate statistics
        total_cases = len(analyses)
        category_counts = {}
        avg_confidence = 0.0
        
        for analysis in analyses:
            category_counts[analysis.error_category] = category_counts.get(analysis.error_category, 0) + 1
            avg_confidence += analysis.confidence_score
        
        avg_confidence /= total_cases if total_cases > 0 else 1
        
        # Generate report
        report_content = f"""
{'='*80}
META PROMPTING ERROR ANALYSIS REPORT
{'='*80}

Dataset: {dataset.upper()}
Analysis Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Total Error Cases Analyzed: {total_cases}
Average Analysis Confidence: {avg_confidence:.2f}

{'='*80}
EXECUTIVE SUMMARY
{'='*80}

This report analyzes {total_cases} cases where meta prompting failed to extract 
proper answers (gem_eval_extracted_response = No) and achieved F1 scores below 80.

These failures indicate issues with:
- Answer format compliance (not using "Final Answer: [Answer]" format)
- Meta-reasoning structure violations
- Response parsing and extraction problems
- Incomplete reasoning processes

ERROR CATEGORY DISTRIBUTION:
{'-'*40}
"""
        
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_cases) * 100
            report_content += f"{category.upper().replace('_', ' ')}: {count} cases ({percentage:.1f}%)\n"
        
        report_content += f"""
{'='*80}
DETAILED CASE ANALYSIS
{'='*80}

"""
        
        # Group analyses by category for better organization
        analyses_by_category = {}
        for analysis in analyses:
            if analysis.error_category not in analyses_by_category:
                analyses_by_category[analysis.error_category] = []
            analyses_by_category[analysis.error_category].append(analysis)
        
        # Add detailed analysis for each category
        for category, category_analyses in analyses_by_category.items():
            report_content += f"""
{'-'*60}
CATEGORY: {category.upper().replace('_', ' ')}
{'-'*60}
Cases in this category: {len(category_analyses)}

"""
            for i, analysis in enumerate(category_analyses[:5], 1):  # Show top 5 per category
                report_content += f"""
Case #{i} (ID: {analysis.case_id[-8:]}):
FAILURE REASON: {analysis.failure_reason}

DETAILED ANALYSIS:
{analysis.detailed_analysis}

SUGGESTED IMPROVEMENT:
{analysis.suggested_improvement}

CONFIDENCE: {analysis.confidence_score:.2f}
{'-'*40}
"""
        
        # Add recommendations section
        report_content += f"""
{'='*80}
RECOMMENDATIONS FOR IMPROVEMENT
{'='*80}

Based on the analysis of {total_cases} error cases, here are the key recommendations:

1. **FORMAT ENFORCEMENT IMPROVEMENTS:**
   - Add explicit validation for "Final Answer: [Answer]" format
   - Implement post-processing to detect and fix format violations
   - Include format examples in few-shot prompting for {dataset} dataset

2. **META-REASONING STRUCTURE ENHANCEMENTS:**
   - Strengthen the meta-reasoning prompt structure
   - Add validation checkpoints at each reasoning stage
   - Implement automatic structure compliance checking

3. **ANSWER EXTRACTION ROBUSTNESS:**
   - Improve regex patterns for answer extraction
   - Add fallback extraction methods for edge cases
   - Implement semantic similarity matching for partial answers

4. **RESPONSE COMPLETION SAFEGUARDS:**
   - Add response length validation
   - Implement continuation prompts for truncated responses
   - Monitor for incomplete reasoning chains

5. **DATASET-SPECIFIC OPTIMIZATIONS:**
   - Develop specialized extraction patterns for {dataset}
   - Create validation rules based on expected answer formats
   - Implement domain-specific post-processing steps

{'='*80}
TECHNICAL DETAILS
{'='*80}

Analysis performed using: {analyses[0].__class__.__name__ if analyses else 'N/A'}
Focus: gem_eval_extracted_response = "No" cases with F1 < 80
Report generated: {datetime.now().isoformat()}
Output directory: {self.output_dir}

{'='*80}
END OF REPORT
{'='*80}
"""
        
        # Write report to file
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Comprehensive report generated: {report_file}")
        return str(report_file)
    
    def generate_csv_summary(self, analyses: List[ErrorAnalysis], dataset: str) -> str:
        """Generate CSV summary of all analyses"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = self.output_dir / f"{dataset}_error_summary_{timestamp}.csv"
        
        # Convert to DataFrame
        df = pd.DataFrame([asdict(analysis) for analysis in analyses])
        df.to_csv(csv_file, index=False)
        
        logger.info(f"CSV summary generated: {csv_file}")
        return str(csv_file)


class MetaPromptingErrorAnalyzer:
    """Main orchestrator class for error analysis"""
    
    def __init__(self, config: EnvironmentConfig):
        self.config = config
        self.db_connector = DatabaseConnector(config)
        self.llm_analyzer = None
        self.reporter = None
    
    def setup_analyzer(self, api_provider: str, output_dir: str):
        """Setup LLM analyzer and reporter"""
        self.llm_analyzer = LLMAnalyzer(api_provider, self.config)
        self.reporter = ErrorAnalysisReporter(output_dir)
        self.db_connector.connect()
    
    def analyze_dataset(self, dataset: str, f1_threshold: float = 80.0, max_cases: Optional[int] = None) -> Tuple[str, str]:
        """
        Perform complete error analysis for a dataset
        
        Args:
            dataset: Dataset name
            f1_threshold: F1 score threshold for error cases
            max_cases: Maximum number of cases to analyze (None for all)
            
        Returns:
            Tuple of (report_file_path, csv_file_path)
        """
        if not self.llm_analyzer or not self.reporter:
            raise RuntimeError("Analyzer not properly setup. Call setup_analyzer() first.")
        
        logger.info(f"Starting error analysis for dataset: {dataset}")
        
        # Fetch error cases
        error_cases_data = self.db_connector.get_error_cases(dataset, f1_threshold)
        
        if not error_cases_data:
            logger.warning(f"No error cases found for dataset {dataset}")
            return None, None
        
        # Limit cases if specified
        if max_cases:
            error_cases_data = error_cases_data[:max_cases]
        
        # Convert to ErrorCase objects
        error_cases = []
        for case_data in error_cases_data:
            try:
                error_case = ErrorCase(
                    _id=str(case_data.get('_id', '')),
                    dataset=dataset,
                    question=case_data.get('question', ''),
                    answer=case_data.get('answer', ''),
                    response=case_data.get('response', ''),
                    extracted_response=case_data.get('extracted_response', ''),
                    code_output=case_data.get('code_output', ''),
                    f1_final=case_data.get('f1_final', 0.0),
                    f1_score_extracted_response=case_data.get('f1_score_extracted_response', 0.0),
                    f1_score_code_output=case_data.get('f1_score_code_output', 0.0),
                    reasoning_type=case_data.get('reasoning_type', ''),
                    model=case_data.get('model', ''),
                    q_num=case_data.get('q_num', 0)
                )
                error_cases.append(error_case)
            except Exception as e:
                logger.error(f"Error creating ErrorCase from data: {e}")
                continue
        
        logger.info(f"Analyzing {len(error_cases)} error cases...")
        
        # Perform LLM analysis on each case
        analyses = []
        for error_case in tqdm(error_cases, desc=f"Analyzing {dataset} errors"):
            try:
                analysis = self.llm_analyzer.analyze_error_case(error_case)
                analyses.append(analysis)
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.error(f"Failed to analyze case {error_case._id}: {e}")
                continue
        
        # Generate reports
        report_file = self.reporter.generate_comprehensive_report(analyses, dataset)
        csv_file = self.reporter.generate_csv_summary(analyses, dataset)
        
        logger.info(f"Analysis complete for {dataset}. Generated {len(analyses)} analyses.")
        return report_file, csv_file
    
    def close(self):
        """Clean up resources"""
        self.db_connector.close()


def main():
    """Main function to run the error analysis"""
    parser = argparse.ArgumentParser(description="Meta Prompting Error Analysis")
    parser.add_argument("--dataset", type=str, required=True,
                      choices=["fetaqa", "finqa", "hitabs", "hybridqa", "sqa", "squall", "tatqa", "wiki"],
                      help="Dataset to analyze")
    parser.add_argument("--api_provider", type=str, required=True,
                      choices=["gemini", "openai"],
                      help="LLM API provider")
    parser.add_argument("--output_dir", type=str, default="./analysis_results",
                      help="Output directory for reports")
    parser.add_argument("--f1_threshold", type=float, default=80.0,
                      help="F1 score threshold for error cases")
    parser.add_argument("--max_cases", type=int, default=None,
                      help="Maximum number of cases to analyze")
    parser.add_argument("--env_file", type=str, default=".env",
                      help="Path to environment file (default: .env)")
    
    args = parser.parse_args()
    
    # Load environment file if specified and exists
    if args.env_file and os.path.exists(args.env_file):
        load_dotenv(args.env_file)
        logger.info(f"Loaded environment from: {args.env_file}")
    
    try:
        # Initialize configuration
        config = EnvironmentConfig()
        
        # Validate API provider availability
        try:
            config.get_api_key(args.api_provider)
        except ValueError as e:
            logger.error(f"API configuration error: {e}")
            print(f"\nError: {e}")
            print(f"\nPlease ensure your .env file contains the required API key:")
            if args.api_provider.lower() == 'gemini':
                print("GEMINI_API_KEY=your_gemini_api_key_here")
            else:
                print("OPENAI_API_KEY=your_openai_api_key_here")
            sys.exit(1)
        
        # Create main analyzer
        analyzer = MetaPromptingErrorAnalyzer(config)
        analyzer.setup_analyzer(args.api_provider, args.output_dir)
        
        # Run analysis
        report_file, csv_file = analyzer.analyze_dataset(
            args.dataset, 
            args.f1_threshold, 
            args.max_cases
        )
        
        if report_file and csv_file:
            print(f"\n{'='*60}")
            print("ANALYSIS COMPLETE!")
            print(f"{'='*60}")
            print(f"Dataset: {args.dataset}")
            print(f"API Provider: {args.api_provider}")
            print(f"Report: {report_file}")
            print(f"CSV Summary: {csv_file}")
            print(f"{'='*60}")
        else:
            print(f"No error cases found for dataset: {args.dataset}")
    
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        print(f"\nError: {e}")
        sys.exit(1)
    
    finally:
        if 'analyzer' in locals():
            analyzer.close()


if __name__ == "__main__":
    main()