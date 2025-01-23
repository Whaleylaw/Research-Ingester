import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  VStack,
  Text,
  Card,
  CardBody,
  FormControl,
  FormLabel,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  HStack,
  Select,
  Button,
  Icon,
  useToast,
} from '@chakra-ui/react';
import { FiRefreshCw } from 'react-icons/fi';
import ForceGraph2D from 'react-force-graph-2d';

interface GraphNode {
  id: string;
  label: string;
  type: string;
  tags: string[];
  isNew: boolean;
  confidence: number;
}

interface GraphLink {
  source: string;
  target: string;
  weight: number;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphLink[];
}

const Graph: React.FC = () => {
  const [data, setData] = useState<GraphData>({ nodes: [], edges: [] });
  const [maxNodes, setMaxNodes] = useState(100);
  const [minConfidence, setMinConfidence] = useState(0.5);
  const [colorBy, setColorBy] = useState<'type' | 'novelty'>('type');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const toast = useToast();

  const fetchGraphData = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/graph?max_nodes=${maxNodes}&min_confidence=${minConfidence}`
      );
      if (!response.ok) throw new Error('Failed to fetch graph data');

      const graphData = await response.json();
      setData(graphData);
    } catch (error) {
      toast({
        title: 'Error fetching graph data',
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
    fetchGraphData();
  }, []);

  const getNodeColor = useCallback(
    (node: GraphNode) => {
      if (colorBy === 'type') {
        switch (node.type) {
          case 'pdf':
            return '#E53E3E';
          case 'video':
            return '#38A169';
          case 'audio':
            return '#805AD5';
          case 'web':
            return '#3182CE';
          default:
            return '#718096';
        }
      } else {
        return node.isNew ? '#38A169' : '#3182CE';
      }
    },
    [colorBy]
  );

  const handleNodeClick = useCallback(
    (node: GraphNode) => {
      navigate(`/nodes/${node.id}`);
    },
    [navigate]
  );

  return (
    <VStack spacing={4} h="calc(100vh - 200px)">
      <Card w="full">
        <CardBody>
          <VStack spacing={4} align="stretch">
            <Text fontSize="2xl" fontWeight="bold">
              Knowledge Graph
            </Text>
            <Text color="gray.600">
              Visualize relationships between knowledge nodes
            </Text>

            <HStack spacing={4}>
              <FormControl>
                <FormLabel>Maximum Nodes</FormLabel>
                <NumberInput
                  value={maxNodes}
                  onChange={(_, value) => setMaxNodes(value)}
                  min={10}
                  max={500}
                  step={10}
                >
                  <NumberInputField />
                  <NumberInputStepper>
                    <NumberIncrementStepper />
                    <NumberDecrementStepper />
                  </NumberInputStepper>
                </NumberInput>
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

              <FormControl>
                <FormLabel>Color By</FormLabel>
                <Select
                  value={colorBy}
                  onChange={(e) =>
                    setColorBy(e.target.value as 'type' | 'novelty')
                  }
                >
                  <option value="type">Source Type</option>
                  <option value="novelty">Information Novelty</option>
                </Select>
              </FormControl>

              <FormControl>
                <FormLabel>&nbsp;</FormLabel>
                <Button
                  w="full"
                  onClick={fetchGraphData}
                  isLoading={isLoading}
                  leftIcon={<Icon as={FiRefreshCw} />}
                >
                  Refresh
                </Button>
              </FormControl>
            </HStack>
          </VStack>
        </CardBody>
      </Card>

      <Box
        flex={1}
        w="full"
        bg="white"
        borderRadius="md"
        shadow="sm"
        overflow="hidden"
      >
        <ForceGraph2D
          graphData={data}
          nodeId="id"
          nodeLabel="label"
          nodeColor={(node) => getNodeColor(node as GraphNode)}
          nodeRelSize={8}
          linkWidth={(link) => (link as GraphLink).weight * 2}
          linkColor={() => '#CBD5E0'}
          onNodeClick={(node) => handleNodeClick(node as GraphNode)}
          cooldownTicks={100}
          linkDirectionalParticles={2}
          linkDirectionalParticleWidth={(link) =>
            (link as GraphLink).weight * 2
          }
        />
      </Box>
    </VStack>
  );
};

export default Graph; 