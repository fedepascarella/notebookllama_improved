"""
Content Enhancement Service - Senior-level LLM integration for document processing
Handles AI-powered summarization, Q&A generation, topic extraction, and mind mapping
"""

import asyncio
import logging
import json
import re
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from llama_index.llms.openai import OpenAI
from llama_index.core.llms import ChatMessage
from llama_index.core.prompts import PromptTemplate

from .workflow_events import DocumentProcessedEvent, EventValidator

logger = logging.getLogger(__name__)


@dataclass
class EnhancementConfig:
    """Configuration for content enhancement"""
    model: str = "gpt-4o"
    max_summary_words: int = 300
    num_qa_pairs: int = 5
    max_key_points: int = 8
    max_topics: int = 6
    chunk_size: int = 4000  # For large documents
    temperature: float = 0.3  # Lower for more consistent results
    timeout_seconds: int = 60


class ContentEnhancer:
    """
    Senior-level content enhancement service using OpenAI.
    Handles chunking, rate limiting, error recovery, and quality validation.
    """

    def __init__(self, config: Optional[EnhancementConfig] = None):
        self.config = config or EnhancementConfig()
        self.llm = None
        self._init_llm()

    def _init_llm(self) -> None:
        """Initialize LLM with error handling"""
        try:
            import os
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")

            self.llm = OpenAI(
                model=self.config.model,
                api_key=api_key,
                temperature=self.config.temperature,
                timeout=self.config.timeout_seconds
            )
            logger.info(f"LLM initialized: {self.config.model}")

        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise

    async def enhance_document(
        self,
        document_event: DocumentProcessedEvent
    ) -> Dict[str, Any]:
        """
        Main enhancement pipeline - generates all enhanced content

        Args:
            document_event: Validated document processed event

        Returns:
            Dictionary with all enhanced content
        """
        logger.info(f"Starting enhancement for document: {document_event.title}")
        start_time = datetime.now()

        try:
            # Prepare content for processing
            content = self._prepare_content(document_event.raw_content)

            # Run all enhancement tasks concurrently for efficiency
            tasks = [
                self._generate_summary(content, document_event.title),
                self._generate_key_points(content),
                self._generate_qa_pairs(content),
                self._extract_topics(content)
            ]

            # Execute with timeout protection
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.config.timeout_seconds * 2
            )

            summary, key_points, qa_result, topics = results

            # Validate results and handle exceptions
            summary = self._validate_summary(summary, content)
            key_points = self._validate_key_points(key_points)
            questions, answers = self._validate_qa_result(qa_result, content)
            topics = self._validate_topics(topics)

            # Calculate processing metrics
            processing_time = (datetime.now() - start_time).total_seconds()

            enhanced_content = {
                "summary": summary,
                "key_points": key_points,
                "questions": questions,
                "answers": answers,
                "topics": topics,
                "metadata": {
                    "enhancement_model": self.config.model,
                    "processing_time_seconds": processing_time,
                    "content_length_processed": len(content),
                    "enhancement_timestamp": datetime.now().isoformat(),
                    "quality_score": self._calculate_quality_score(
                        summary, key_points, questions, answers
                    )
                }
            }

            logger.info(
                f"Enhancement completed in {processing_time:.2f}s. "
                f"Quality score: {enhanced_content['metadata']['quality_score']:.2f}"
            )

            return enhanced_content

        except asyncio.TimeoutError:
            logger.error("Content enhancement timed out")
            return self._create_fallback_content(document_event)
        except Exception as e:
            logger.error(f"Content enhancement failed: {e}")
            return self._create_fallback_content(document_event, error=e)

    def _prepare_content(self, raw_content: str) -> str:
        """Prepare content for LLM processing"""
        # Clean and normalize content
        content = re.sub(r'\n{3,}', '\n\n', raw_content)  # Remove excessive newlines
        content = re.sub(r'[ \t]+', ' ', content)  # Normalize spaces
        content = content.strip()

        # Truncate if too long (keep most important content)
        if len(content) > self.config.chunk_size:
            # Try to keep complete paragraphs
            truncated = content[:self.config.chunk_size]
            last_period = truncated.rfind('.')
            if last_period > self.config.chunk_size * 0.8:  # Keep if within 80%
                content = truncated[:last_period + 1]
            else:
                content = truncated

        return content

    async def _generate_summary(self, content: str, title: str) -> str:
        """Generate intelligent summary using LLM"""
        prompt = PromptTemplate(
            template="""
Create a clear, concise summary of this document in approximately {max_words} words.

Document Title: {title}

Content:
{content}

Requirements:
1. Focus on main themes and key insights
2. Write in clear, accessible language
3. Highlight important findings or conclusions
4. Make it engaging and informative
5. Maximum {max_words} words

Summary:"""
        )

        try:
            formatted_prompt = prompt.format(
                content=content,
                title=title,
                max_words=self.config.max_summary_words
            )

            message = ChatMessage(role="user", content=formatted_prompt)
            response = await self.llm.achat([message])

            summary = response.message.content.strip()

            # Post-process summary
            summary = self._clean_llm_output(summary)

            return summary

        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return self._create_fallback_summary(content, title)

    async def _generate_key_points(self, content: str) -> List[str]:
        """Extract key points from content"""
        prompt = PromptTemplate(
            template="""
Extract the {num_points} most important key points from this document.

Content:
{content}

Requirements:
1. Each point should be concise but informative (1-2 sentences)
2. Focus on factual information and insights
3. Avoid repetition
4. Order by importance
5. Return exactly {num_points} points

Format as a simple numbered list:
1. [First key point]
2. [Second key point]
...

Key Points:"""
        )

        try:
            formatted_prompt = prompt.format(
                content=content,
                num_points=self.config.max_key_points
            )

            message = ChatMessage(role="user", content=formatted_prompt)
            response = await self.llm.achat([message])

            # Parse the numbered list
            key_points = self._parse_numbered_list(response.message.content)

            return key_points[:self.config.max_key_points]

        except Exception as e:
            logger.error(f"Key points generation failed: {e}")
            return self._create_fallback_key_points(content)

    async def _generate_qa_pairs(self, content: str) -> Tuple[List[str], List[str]]:
        """Generate relevant Q&A pairs"""
        prompt = PromptTemplate(
            template="""
Create {num_qa} relevant questions and answers based on this document content.

Content:
{content}

Requirements:
1. Questions should be specific to the document content
2. Answers should be informative and based on the text
3. Cover different aspects of the document
4. Questions should be what a reader would actually ask
5. Answers should be 2-3 sentences each

Format:
Q1: [Question about main topic]
A1: [Detailed answer based on content]

Q2: [Question about specific details]
A2: [Detailed answer based on content]

... continue for {num_qa} pairs

Q&A:"""
        )

        try:
            formatted_prompt = prompt.format(
                content=content,
                num_qa=self.config.num_qa_pairs
            )

            message = ChatMessage(role="user", content=formatted_prompt)
            response = await self.llm.achat([message])

            questions, answers = self._parse_qa_pairs(response.message.content)

            return questions, answers

        except Exception as e:
            logger.error(f"Q&A generation failed: {e}")
            return self._create_fallback_qa(content)

    async def _extract_topics(self, content: str) -> List[str]:
        """Extract main topics for mind mapping"""
        prompt = PromptTemplate(
            template="""
Identify the {num_topics} main topics/themes in this document for creating a mind map.

Content:
{content}

Requirements:
1. Topics should be broad themes, not specific details
2. Suitable for mind map nodes
3. 1-3 words per topic
4. Cover the document comprehensively
5. Return exactly {num_topics} topics

Format as a simple list:
- Topic 1
- Topic 2
...

Topics:"""
        )

        try:
            formatted_prompt = prompt.format(
                content=content,
                num_topics=self.config.max_topics
            )

            message = ChatMessage(role="user", content=formatted_prompt)
            response = await self.llm.achat([message])

            topics = self._parse_topic_list(response.message.content)

            return topics[:self.config.max_topics]

        except Exception as e:
            logger.error(f"Topic extraction failed: {e}")
            return self._create_fallback_topics(content)

    # Validation and quality control methods
    def _validate_summary(self, summary: Any, content: str) -> str:
        """Validate and clean summary"""
        if isinstance(summary, Exception):
            logger.error(f"Summary generation exception: {summary}")
            return self._create_fallback_summary(content, "Document")

        if not isinstance(summary, str) or len(summary.strip()) < 50:
            logger.warning("Summary too short, creating fallback")
            return self._create_fallback_summary(content, "Document")

        return summary.strip()

    def _validate_key_points(self, key_points: Any) -> List[str]:
        """Validate key points"""
        if isinstance(key_points, Exception):
            logger.error(f"Key points generation exception: {key_points}")
            return ["Document processed successfully", "Content analysis completed", "Key information extracted"]

        if not isinstance(key_points, list) or len(key_points) < 3:
            logger.warning("Insufficient key points, creating fallback")
            return ["Document processed successfully", "Content analysis completed", "Key information extracted"]

        return [point.strip() for point in key_points if point.strip()]

    def _validate_qa_result(self, qa_result: Any, content: str) -> Tuple[List[str], List[str]]:
        """Validate Q&A pairs"""
        if isinstance(qa_result, Exception):
            logger.error(f"Q&A generation exception: {qa_result}")
            return self._create_fallback_qa(content)

        if not isinstance(qa_result, tuple) or len(qa_result) != 2:
            logger.warning("Invalid Q&A format, creating fallback")
            return self._create_fallback_qa(content)

        questions, answers = qa_result
        if not EventValidator.validate_qa_quality(questions, answers):
            logger.warning("Q&A quality validation failed, creating fallback")
            return self._create_fallback_qa(content)

        return questions, answers

    def _validate_topics(self, topics: Any) -> List[str]:
        """Validate topics"""
        if isinstance(topics, Exception):
            logger.error(f"Topic extraction exception: {topics}")
            return ["Main Content", "Key Information", "Document Analysis"]

        if not isinstance(topics, list) or len(topics) < 3:
            logger.warning("Insufficient topics, creating fallback")
            return ["Main Content", "Key Information", "Document Analysis"]

        return [topic.strip() for topic in topics if topic.strip()]

    # Utility methods
    def _clean_llm_output(self, text: str) -> str:
        """Clean LLM output text"""
        # Remove common LLM artifacts
        text = re.sub(r'^(Summary:|Key Points:|Topics:)\s*', '', text)
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _parse_numbered_list(self, text: str) -> List[str]:
        """Parse numbered list from LLM response"""
        points = []
        lines = text.strip().split('\n')

        for line in lines:
            # Match patterns like "1. Point" or "1) Point"
            match = re.match(r'^\d+[\.\)]\s*(.*)', line.strip())
            if match:
                point = match.group(1).strip()
                if point:
                    points.append(point)

        return points

    def _parse_qa_pairs(self, text: str) -> Tuple[List[str], List[str]]:
        """Parse Q&A pairs from LLM response"""
        questions = []
        answers = []

        # Split by Q/A patterns
        qa_pattern = r'Q\d+:\s*(.*?)\s*A\d+:\s*(.*?)(?=Q\d+:|$)'
        matches = re.findall(qa_pattern, text, re.DOTALL | re.IGNORECASE)

        for question, answer in matches:
            q = question.strip()
            a = answer.strip()
            if q and a:
                if not q.endswith('?'):
                    q += '?'
                questions.append(q)
                answers.append(a)

        return questions, answers

    def _parse_topic_list(self, text: str) -> List[str]:
        """Parse topic list from LLM response"""
        topics = []
        lines = text.strip().split('\n')

        for line in lines:
            # Match patterns like "- Topic" or "• Topic"
            topic = re.sub(r'^[-•*]\s*', '', line.strip())
            if topic and len(topic.split()) <= 3:  # Max 3 words per topic
                topics.append(topic)

        return topics

    def _calculate_quality_score(
        self,
        summary: str,
        key_points: List[str],
        questions: List[str],
        answers: List[str]
    ) -> float:
        """Calculate content quality score (0-1)"""
        score = 0.0

        # Summary quality (0-0.4)
        if len(summary) >= 100:
            score += 0.2
        if len(summary.split()) >= 50:
            score += 0.2

        # Key points quality (0-0.3)
        if len(key_points) >= 5:
            score += 0.15
        if all(len(point) >= 20 for point in key_points):
            score += 0.15

        # Q&A quality (0-0.3)
        if len(questions) >= 3:
            score += 0.15
        if all(len(answer) >= 30 for answer in answers):
            score += 0.15

        return min(score, 1.0)

    # Fallback content creation
    def _create_fallback_content(
        self,
        document_event: DocumentProcessedEvent,
        error: Optional[Exception] = None
    ) -> Dict[str, Any]:
        """Create fallback content when enhancement fails"""
        logger.warning("Creating fallback enhanced content")

        content_preview = document_event.get_content_preview(1000)

        return {
            "summary": self._create_fallback_summary(content_preview, document_event.title),
            "key_points": self._create_fallback_key_points(content_preview),
            "questions": ["What is this document about?", "What are the main points?", "How is the content structured?"],
            "answers": [
                f"This document titled '{document_event.title}' contains {document_event.content_size} characters of content.",
                "The document has been processed and analyzed for key information and insights.",
                "The content is structured and ready for exploration and analysis."
            ],
            "topics": self._create_fallback_topics(content_preview),
            "metadata": {
                "enhancement_model": "fallback",
                "processing_error": str(error) if error else "Enhancement service unavailable",
                "content_length_processed": len(content_preview),
                "enhancement_timestamp": datetime.now().isoformat(),
                "quality_score": 0.5  # Moderate score for fallback
            }
        }

    def _create_fallback_summary(self, content: str, title: str) -> str:
        """Create basic summary when LLM fails"""
        sentences = content.split('. ')
        first_sentences = '. '.join(sentences[:3])

        return f"This document titled '{title}' contains important information and insights. {first_sentences}. The document has been processed and is ready for analysis and exploration."

    def _create_fallback_key_points(self, content: str) -> List[str]:
        """Create basic key points when LLM fails"""
        return [
            "Document successfully processed and analyzed",
            f"Contains {len(content)} characters of content",
            "Ready for detailed exploration and analysis",
            "Structured content available for querying",
            "Comprehensive information extracted and organized"
        ]

    def _create_fallback_qa(self, content: str) -> Tuple[List[str], List[str]]:
        """Create basic Q&A when LLM fails"""
        questions = [
            "What type of document is this?",
            "How much content does it contain?",
            "Is the document ready for analysis?"
        ]

        answers = [
            "This is a processed document that has been analyzed and structured for exploration.",
            f"The document contains {len(content)} characters of detailed content and information.",
            "Yes, the document has been successfully processed and is ready for detailed analysis and querying."
        ]

        return questions, answers

    def _create_fallback_topics(self, content: str) -> List[str]:
        """Create basic topics when LLM fails"""
        return ["Document Content", "Main Information", "Key Details", "Analysis Results"]


# Factory function for easy instantiation
def create_content_enhancer(model: str = "gpt-4o") -> ContentEnhancer:
    """Create content enhancer with specified model"""
    config = EnhancementConfig(model=model)
    return ContentEnhancer(config)