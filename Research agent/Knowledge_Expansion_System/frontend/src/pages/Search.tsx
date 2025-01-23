import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  SimpleGrid,
  Text,
  Select,
  Switch,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Card,
  CardBody,
  Badge,
  HStack,
  Icon,
  useToast,
} from '@chakra-ui/react';
import { FiSearch, FiTag, FiFile, FiStar } from 'react-icons/fi';
import { Link as RouterLink } from 'react-router-dom';

interface SearchResult {
  id: string;
  title: string;
  summary: string;
  tags: string[];
  source_type: string;
  is_new_information: boolean;
  confidence_score: number;
}

const Search: React.FC = () => {
  const [keywords, setKeywords] = useState('');
  const [tags, setTags] = useState('');
  const [sourceType, setSourceType] = useState('');
  const [onlyNew, setOnlyNew] = useState(false);
  const [minConfidence, setMinConfidence] = useState(0.5);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();

  const handleSearch = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        ...(keywords && { keywords }),
        ...(tags && { tags }),
        ...(sourceType && { source_type: sourceType }),
        ...(onlyNew && { only_new: 'true' }),
        ...(minConfidence && { min_confidence: minConfidence.toString() }),
      });

      const response = await fetch(`http://localhost:8000/search?${params}`);
      if (!response.ok) throw new Error('Search failed');

      const data = await response.json();
      setResults(data);
    } catch (error) {
      toast({
        title: 'Search failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    handleSearch();
  }, []);

  return (
    <VStack spacing={8} align="stretch">
      <Text fontSize="2xl" fontWeight="bold">
        Search Knowledge Base
      </Text>

      <Card>
        <CardBody>
          <VStack spacing={4} align="stretch">
            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
              <FormControl>
                <FormLabel>Keywords</FormLabel>
                <Input
                  placeholder="Search by keywords..."
                  value={keywords}
                  onChange={(e) => setKeywords(e.target.value)}
                  leftElement={<Icon as={FiSearch} color="gray.500" ml={2} />}
                />
              </FormControl>

              <FormControl>
                <FormLabel>Tags</FormLabel>
                <Input
                  placeholder="Comma-separated tags..."
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  leftElement={<Icon as={FiTag} color="gray.500" ml={2} />}
                />
              </FormControl>

              <FormControl>
                <FormLabel>Source Type</FormLabel>
                <Select
                  placeholder="All sources"
                  value={sourceType}
                  onChange={(e) => setSourceType(e.target.value)}
                >
                  <option value="pdf">PDF</option>
                  <option value="video">Video</option>
                  <option value="audio">Audio</option>
                  <option value="web">Web</option>
                </Select>
              </FormControl>

              <FormControl>
                <FormLabel>Minimum Confidence</FormLabel>
                <NumberInput
                  value={minConfidence}
                  onChange={(_, value) => setMinConfidence(value)}
                  min={0}
                  max={1}
                  step={0.1}
                >
                  <NumberInputField />
                  <NumberInputStepper>
                    <NumberIncrementStepper />
                    <NumberDecrementStepper />
                  </NumberInputStepper>
                </NumberInput>
              </FormControl>
            </SimpleGrid>

            <FormControl display="flex" alignItems="center">
              <FormLabel mb="0">Only New Information</FormLabel>
              <Switch
                isChecked={onlyNew}
                onChange={(e) => setOnlyNew(e.target.checked)}
              />
            </FormControl>

            <Button
              colorScheme="blue"
              onClick={handleSearch}
              isLoading={isLoading}
              leftIcon={<Icon as={FiSearch} />}
            >
              Search
            </Button>
          </VStack>
        </CardBody>
      </Card>

      <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
        {results.map((result) => (
          <Card
            key={result.id}
            as={RouterLink}
            to={`/nodes/${result.id}`}
            _hover={{ transform: 'translateY(-2px)', shadow: 'lg' }}
            transition="all 0.2s"
          >
            <CardBody>
              <VStack align="stretch" spacing={3}>
                <HStack justify="space-between">
                  <Text fontSize="lg" fontWeight="semibold" noOfLines={1}>
                    {result.title}
                  </Text>
                  <Badge
                    colorScheme={result.is_new_information ? 'green' : 'blue'}
                    display="flex"
                    alignItems="center"
                  >
                    <Icon
                      as={result.is_new_information ? FiStar : FiFile}
                      mr={1}
                    />
                    {result.is_new_information ? 'New' : 'Existing'}
                  </Badge>
                </HStack>

                <Text noOfLines={3} color="gray.600">
                  {result.summary}
                </Text>

                <HStack spacing={2} flexWrap="wrap">
                  {result.tags.map((tag) => (
                    <Badge key={tag} colorScheme="blue">
                      {tag}
                    </Badge>
                  ))}
                </HStack>

                <HStack justify="space-between">
                  <Badge colorScheme="purple">{result.source_type}</Badge>
                  <Text fontSize="sm" color="gray.500">
                    Confidence: {(result.confidence_score * 100).toFixed(0)}%
                  </Text>
                </HStack>
              </VStack>
            </CardBody>
          </Card>
        ))}
      </SimpleGrid>
    </VStack>
  );
};

export default Search; 