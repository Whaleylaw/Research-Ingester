import React, { useState, useRef, useEffect } from 'react';
import {
  VStack,
  Box,
  Input,
  Button,
  Text,
  Card,
  CardBody,
  Icon,
  useToast,
  List,
  ListItem,
  Divider,
  Switch,
  FormControl,
  FormLabel,
  HStack,
} from '@chakra-ui/react';
import { FiSend, FiUser, FiDatabase } from 'react-icons/fi';

interface Message {
  type: 'user' | 'assistant';
  content: string;
  confidence?: number;
  sources?: string[];
}

const Query: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showSources, setShowSources] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const toast = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input;
    setInput('');
    setMessages((prev) => [...prev, { type: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: userMessage,
          include_sources: showSources,
        }),
      });

      if (!response.ok) throw new Error('Query failed');

      const data = await response.json();
      setMessages((prev) => [
        ...prev,
        {
          type: 'assistant',
          content: data.response,
          confidence: data.confidence,
          sources: data.sources,
        },
      ]);
    } catch (error) {
      toast({
        title: 'Query failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <VStack spacing={4} h="calc(100vh - 200px)">
      <Card w="full">
        <CardBody>
          <VStack spacing={4} align="stretch">
            <Text fontSize="2xl" fontWeight="bold">
              Query Knowledge Base
            </Text>
            <Text color="gray.600">
              Ask questions in natural language to explore and analyze the knowledge base
            </Text>
            <FormControl display="flex" alignItems="center">
              <FormLabel mb="0">Show Sources</FormLabel>
              <Switch
                isChecked={showSources}
                onChange={(e) => setShowSources(e.target.checked)}
              />
            </FormControl>
          </VStack>
        </CardBody>
      </Card>

      <Box
        flex={1}
        w="full"
        overflowY="auto"
        bg="white"
        borderRadius="md"
        shadow="sm"
        p={4}
      >
        <List spacing={4}>
          {messages.map((message, index) => (
            <ListItem key={index}>
              <HStack
                align="flex-start"
                spacing={4}
                bg={message.type === 'assistant' ? 'blue.50' : 'gray.50'}
                p={4}
                borderRadius="md"
              >
                <Icon
                  as={message.type === 'assistant' ? FiDatabase : FiUser}
                  boxSize={6}
                  color={message.type === 'assistant' ? 'blue.500' : 'gray.500'}
                />
                <VStack align="stretch" flex={1} spacing={2}>
                  <Text whiteSpace="pre-wrap">{message.content}</Text>
                  {message.type === 'assistant' && (
                    <>
                      {message.confidence !== undefined && (
                        <Text fontSize="sm" color="gray.500">
                          Confidence: {(message.confidence * 100).toFixed(0)}%
                        </Text>
                      )}
                      {showSources && message.sources && message.sources.length > 0 && (
                        <>
                          <Divider />
                          <Text fontSize="sm" fontWeight="medium">
                            Sources:
                          </Text>
                          <List spacing={1}>
                            {message.sources.map((source, idx) => (
                              <ListItem
                                key={idx}
                                fontSize="sm"
                                color="gray.600"
                              >
                                • {source}
                              </ListItem>
                            ))}
                          </List>
                        </>
                      )}
                    </>
                  )}
                </VStack>
              </HStack>
            </ListItem>
          ))}
          <div ref={messagesEndRef} />
        </List>
      </Box>

      <Card w="full">
        <CardBody>
          <form onSubmit={handleSubmit}>
            <HStack>
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask a question..."
                disabled={isLoading}
              />
              <Button
                type="submit"
                colorScheme="blue"
                isLoading={isLoading}
                leftIcon={<Icon as={FiSend} />}
                disabled={!input.trim() || isLoading}
              >
                Send
              </Button>
            </HStack>
          </form>
        </CardBody>
      </Card>
    </VStack>
  );
};

export default Query; 