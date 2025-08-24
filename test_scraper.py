#!/usr/bin/env python3
"""
Test script for the Book Scraper service
"""
import asyncio
import json
from typing import List

from app.core.scraper_engine import ScraperEngine, ScrapingTask
from app.models.book import BookSource


async def test_single_scrape():
    """Test scraping a single book"""
    print("🧪 Testing single book scraping...")
    
    async with ScraperEngine() as engine:
        # Create a test task
        task = ScrapingTask(
            url="https://www.goodreads.com/book/show/3.Harry_Potter_and_the_Sorcerer_s_Stone",
            source=BookSource.GOODREADS,
            priority=1
        )
        
        # Add task and process
        task_id = await engine.add_task(task)
        print(f"📝 Added task: {task_id}")
        
        # Process the task
        await engine.start_processing(1)
        
        # Wait for completion
        await engine.wait_for_completion()
        
        # Get results
        results = engine.get_results()
        failed = engine.get_failed_results()
        
        print(f"✅ Completed tasks: {len(results)}")
        print(f"❌ Failed tasks: {len(failed)}")
        
        if results:
            result = results[0]
            print(f"📚 Scraped book: {result.book.metadata.title if result.book else 'No book data'}")
            print(f"🌐 Source: {result.source}")
            print(f"⏱️  Response time: {result.response_time_ms:.2f}ms")
            print(f"📊 Data size: {result.data_size_bytes} bytes")
        
        # Print stats
        stats = engine.get_stats()
        print(f"📈 Success rate: {stats['success_rate']:.2%}")
        print(f"🚀 Requests per second: {stats['requests_per_second']:.2f}")


async def test_batch_scrape():
    """Test batch scraping"""
    print("\n🧪 Testing batch scraping...")
    
    async with ScraperEngine() as engine:
        # Create multiple test tasks
        test_urls = [
            "https://www.goodreads.com/book/show/3.Harry_Potter_and_the_Sorcerer_s_Stone",
            "https://www.goodreads.com/book/show/5.Harry_Potter_and_the_Prisoner_of_Azkaban",
            "https://www.goodreads.com/book/show/2.Harry_Potter_and_the_Chamber_of_Secrets"
        ]
        
        tasks = []
        for url in test_urls:
            task = ScrapingTask(
                url=url,
                source=BookSource.GOODREADS,
                priority=5
            )
            tasks.append(task)
        
        # Add all tasks
        task_ids = await engine.add_batch_tasks(tasks)
        print(f"📝 Added {len(task_ids)} tasks")
        
        # Process all tasks
        await engine.start_processing(len(tasks))
        
        # Wait for completion
        await engine.wait_for_completion()
        
        # Get results
        results = engine.get_results()
        failed = engine.get_failed_results()
        
        print(f"✅ Completed tasks: {len(results)}")
        print(f"❌ Failed tasks: {len(failed)}")
        
        # Print book titles
        for i, result in enumerate(results):
            if result.book and result.book.metadata:
                print(f"📚 Book {i+1}: {result.book.metadata.title}")
                if result.book.metadata.authors:
                    print(f"   👤 Authors: {', '.join(result.book.metadata.authors)}")
                if result.book.metadata.rating:
                    print(f"   ⭐ Rating: {result.book.metadata.rating}/5")
        
        # Print stats
        stats = engine.get_stats()
        print(f"📈 Success rate: {stats['success_rate']:.2%}")
        print(f"🚀 Requests per second: {stats['requests_per_second']:.2f}")


async def test_rate_limiting():
    """Test rate limiting functionality"""
    print("\n🧪 Testing rate limiting...")
    
    async with ScraperEngine() as engine:
        # Create many tasks to test rate limiting
        test_urls = [
            "https://www.goodreads.com/book/show/3.Harry_Potter_and_the_Sorcerer_s_Stone"
        ] * 10  # 10 requests to the same domain
        
        tasks = []
        for i, url in enumerate(test_urls):
            task = ScrapingTask(
                url=url,
                source=BookSource.GOODREADS,
                priority=5
            )
            tasks.append(task)
        
        # Add all tasks
        task_ids = await engine.add_batch_tasks(tasks)
        print(f"📝 Added {len(task_ids)} tasks to test rate limiting")
        
        # Process all tasks
        await engine.start_processing(len(tasks))
        
        # Wait for completion
        await engine.wait_for_completion()
        
        # Get results
        results = engine.get_results()
        failed = engine.get_failed_results()
        
        print(f"✅ Completed tasks: {len(results)}")
        print(f"❌ Failed tasks: {len(failed)}")
        
        # Print rate limiter stats
        stats = engine.get_stats()
        rate_limiter_stats = stats.get('rate_limiter_stats', {})
        
        print("📊 Rate Limiter Statistics:")
        for domain, domain_stats in rate_limiter_stats.items():
            print(f"   🌐 {domain}:")
            print(f"      📈 Requests: {domain_stats.get('total_requests', 0)}")
            print(f"      🚫 Blocked: {domain_stats.get('blocked_requests', 0)}")
            print(f"      ✅ Success rate: {domain_stats.get('success_rate', 0):.2%}")


async def main():
    """Main test function"""
    print("🚀 Book Scraper Test Suite")
    print("=" * 50)
    
    try:
        # Test single scraping
        await test_single_scrape()
        
        # Test batch scraping
        await test_batch_scrape()
        
        # Test rate limiting
        await test_rate_limiting()
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the test suite
    asyncio.run(main()) 