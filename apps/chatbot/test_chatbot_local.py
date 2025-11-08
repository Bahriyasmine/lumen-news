"""
Test Lumen News Chatbot INSIDE Docker container
Run: docker-compose exec web python test_chatbot_docker.py

This uses the existing Docker environment - no local setup needed!
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

print("=" * 80)
print("🐳 TESTING LUMEN NEWS CHATBOT INSIDE DOCKER")
print("=" * 80)

try:
    from apps.chatbot.chatbot_rag import get_chatbot
    
    print("\n✅ Imports successful!")
    print("\n🚀 Initializing Lumen News chatbot...")
    
    # Get chatbot instance
    chatbot = get_chatbot()
    
    # Test 1: System Statistics
    print("\n" + "=" * 80)
    print("📊 SYSTEM STATISTICS")
    print("=" * 80)
    stats = chatbot.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Test 2: Retrieval Test
    print("\n" + "=" * 80)
    print("🔍 RETRIEVAL TEST - Checking hybrid search")
    print("=" * 80)
    
    test_queries = [
        "player of the year",
        "health innovations",
        "technology news"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        docs = chatbot._hybrid_search(query, k=3)
        print(f"Retrieved {len(docs)} documents:")
        for i, doc in enumerate(docs, 1):
            print(f"  [{i}] {doc.metadata['title']}")
            print(f"      Category: {doc.metadata['category']} | Source: {doc.metadata['source']}")
    
    # Test 3: Chat Tests with Natural Source Integration
    print("\n" + "=" * 80)
    print("💬 CHAT TESTS - Natural Source Integration")
    print("=" * 80)
    
    test_questions = [
        "Who won player of the year 2025?",
        "Tell me about recent health breakthroughs",
        "What's the latest in technology?",
        "Any political developments?",
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*80}")
        print(f"Question {i}: {question}")
        print('='*80)
        
        result = chatbot.chat(question)
        
        if result['success']:
            print(f"\n✅ Response:")
            print(f"{result['response']}")
            
            # Backend info (not shown to user)
            if result['sources']:
                print(f"\n📊 [Backend] Used {len(result['sources'])} sources:")
                for j, source in enumerate(result['sources'], 1):
                    print(f"  [{j}] {source['title']} ({source['source']})")
        else:
            print(f"❌ Error: {result['response']}")
        
        print()
    
    # Test 4: Interactive Mode
    print("\n" + "=" * 80)
    print("🎮 INTERACTIVE MODE")
    print("Type your questions (or 'quit' to exit)")
    print("=" * 80)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            result = chatbot.chat(user_input)
            
            if result['success']:
                print(f"\nLumen: {result['response']}")
            else:
                print(f"\n❌ Error: {result['response']}")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ ERROR OCCURRED: {e}")
    import traceback
    traceback.print_exc()
    print("\n💡 Troubleshooting:")
    print("  1. Check if PostgreSQL is running: docker-compose ps")
    print("  2. Check if news_data.json exists in the right location")
    print("  3. Verify GROQ_API_KEY is set in .env file")
    print("  4. Check vector store initialization")
    print("\n🔧 Quick fixes:")
    print("  - Restart containers: docker-compose restart")
    print("  - Check logs: docker-compose logs web")
    print("  - Rebuild: docker-compose up --build")