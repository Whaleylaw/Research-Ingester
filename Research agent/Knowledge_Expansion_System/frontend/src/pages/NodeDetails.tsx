import React, { useState, useEffect } from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
import {
  VStack,
  Box,
  Text,
  Card,
  CardBody,
  Badge,
  HStack,
  Icon,
  SimpleGrid,
  Divider,
  Button,
  Link,
  Skeleton,
  useToast,
} from '@chakra-ui/react';
import {
  FiExternalLink,
  FiTag,
  FiFile,
  FiStar,
  FiLink,
} from 'react-icons/fi';

interface NodeDetails {
  id: string;
  title: string;
  summary: string;
  tags: string[];
  source_type: string;
  source_path: string;
  is_new_information: boolean;
  confidence_score: number;
  related_nodes: string[];
}

const NodeDetails: React.FC = () => {
  const { nodeId } = useParams<{ nodeId: string }>();
  const [node, setNode] = useState<NodeDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [relatedNodes, setRelatedNodes] = useState<NodeDetails[]>([]);
  const toast = useToast();

  useEffect(() => {
    const fetchNodeDetails = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(
          `http://localhost:8000/nodes/${nodeId}`
        );
        if (!response.ok) throw new Error('Failed to fetch node details');

        const data = await response.json();
        setNode(data);

        // Fetch related nodes
        const relatedPromises = data.related_nodes.map((id: string) =>
          fetch(`http://localhost:8000/nodes/${id}`).then((r) => r.json())
        );
        const relatedData = await Promise.all(relatedPromises);
        setRelatedNodes(relatedData);
      } catch (error) {
        toast({
          title: 'Error fetching node details',
          description: error instanceof Error ? error.message : 'Unknown error',
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
      } finally {
        setIsLoading(false);
      }
    };

    if (nodeId) {
      fetchNodeDetails();
    }
  }, [nodeId, toast]);

  if (isLoading) {
    return (
      <VStack spacing={4}>
        <Skeleton height="40px" width="full" />
        <Skeleton height="200px" width="full" />
        <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4} width="full">
          <Skeleton height="200px" />
          <Skeleton height="200px" />
        </SimpleGrid>
      </VStack>
    );
  }

  if (!node) {
    return (
      <Card>
        <CardBody>
          <Text>Node not found</Text>
        </CardBody>
      </Card>
    );
  }

  return (
    <VStack spacing={4}>
      <Card w="full">
        <CardBody>
          <VStack align="stretch" spacing={4}>
            <HStack justify="space-between">
              <Text fontSize="2xl" fontWeight="bold">
                {node.title}
              </Text>
              <Badge
                colorScheme={node.is_new_information ? 'green' : 'blue'}
                display="flex"
                alignItems="center"
              >
                <Icon
                  as={node.is_new_information ? FiStar : FiFile}
                  mr={1}
                />
                {node.is_new_information ? 'New Information' : 'Existing Knowledge'}
              </Badge>
            </HStack>

            <HStack spacing={2} flexWrap="wrap">
              <Badge colorScheme="purple" display="flex" alignItems="center">
                <Icon as={FiFile} mr={1} />
                {node.source_type}
              </Badge>
              <Badge colorScheme="orange">
                Confidence: {(node.confidence_score * 100).toFixed(0)}%
              </Badge>
              {node.tags.map((tag) => (
                <Badge key={tag} colorScheme="blue">
                  <Icon as={FiTag} mr={1} />
                  {tag}
                </Badge>
              ))}
            </HStack>

            <Box>
              <Text fontWeight="medium">Summary</Text>
              <Text color="gray.600">{node.summary}</Text>
            </Box>

            <Box>
              <Text fontWeight="medium">Source</Text>
              <Link
                href={node.source_path}
                isExternal
                color="blue.500"
                display="flex"
                alignItems="center"
              >
                {node.source_path}
                <Icon as={FiExternalLink} ml={1} />
              </Link>
            </Box>
          </VStack>
        </CardBody>
      </Card>

      {relatedNodes.length > 0 && (
        <Card w="full">
          <CardBody>
            <VStack align="stretch" spacing={4}>
              <Text fontSize="xl" fontWeight="bold">
                Related Content
              </Text>
              <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
                {relatedNodes.map((related) => (
                  <Card
                    key={related.id}
                    as={RouterLink}
                    to={`/nodes/${related.id}`}
                    variant="outline"
                    _hover={{ shadow: 'md' }}
                  >
                    <CardBody>
                      <VStack align="stretch" spacing={2}>
                        <HStack justify="space-between">
                          <Text fontWeight="medium" noOfLines={1}>
                            {related.title}
                          </Text>
                          <Badge colorScheme="purple">
                            {related.source_type}
                          </Badge>
                        </HStack>
                        <Text fontSize="sm" color="gray.600" noOfLines={2}>
                          {related.summary}
                        </Text>
                      </VStack>
                    </CardBody>
                  </Card>
                ))}
              </SimpleGrid>
            </VStack>
          </CardBody>
        </Card>
      )}

      <HStack spacing={4}>
        <Button
          as={RouterLink}
          to="/search"
          variant="outline"
          leftIcon={<Icon as={FiFile} />}
        >
          Back to Search
        </Button>
        <Button
          as={RouterLink}
          to="/graph"
          colorScheme="blue"
          leftIcon={<Icon as={FiLink} />}
        >
          View in Graph
        </Button>
      </HStack>
    </VStack>
  );
};

export default NodeDetails; 