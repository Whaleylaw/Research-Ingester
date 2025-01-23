import React, { useState, useEffect, ChangeEvent, FormEvent } from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  FormHelperText,
  Input,
  Select,
  Switch,
  VStack,
  useToast,
  Card,
  CardBody,
  Text,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Tooltip,
  Icon,
  HStack,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Textarea,
  IconButton,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  SimpleGrid,
  Progress,
  Divider,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  SelectProps,
  NumberInputProps,
} from '@chakra-ui/react';
import { FiInfo, FiCheck, FiX, FiPlus, FiEdit2, FiTrash2, FiRefreshCw } from 'react-icons/fi';
import { Link as RouterLink } from 'react-router-dom';

interface LLMProvider {
  id: string;
  name: string;
}

interface LLMModel {
  provider: string;
  name: string;
  context_window: number;
  capabilities: string[];
  pricing: string | null;
}

interface LLMConfig {
  provider: string;
  model_name: string;
  api_key?: string;
  api_base?: string;
  temperature: number;
  max_tokens?: number;
  context_window?: number;
  streaming: boolean;
}

interface TokenUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  total_cost: number;
}

interface ModelPerformanceMetrics {
  model_name: string;
  average_latency: number;
  token_throughput: number;
  error_rate: number;
  total_requests: number;
  total_tokens: TokenUsage;
  last_updated: string;
}

interface ModelComparison {
  models: string[];
  metrics: Record<string, ModelPerformanceMetrics>;
  benchmark_results: Record<string, Record<string, number>>;
  cost_analysis: Record<string, Record<string, number>>;
}

interface PromptTemplate {
  id: string;
  name: string;
  description: string;
  template: string;
  variables: string[];
  model_name: string;
  temperature: number;
  max_tokens?: number;
  created_at: string;
  last_used?: string;
  usage_count: number;
}

interface FallbackConfig {
  primary_model: string;
  fallback_models: string[];
  fallback_triggers: Record<string, number>;
  max_retries: number;
  timeout_seconds: number;
}

type InputChangeEvent = ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>;
type NumberChangeHandler = (valueAsString: string, valueAsNumber: number) => void;

const LLMConfig: React.FC = () => {
  const [providers, setProviders] = useState<LLMProvider[]>([]);
  const [models, setModels] = useState<LLMModel[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [config, setConfig] = useState<LLMConfig>({
    provider: '',
    model_name: '',
    temperature: 0.7,
    streaming: false,
  });
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();
  const [activeTab, setActiveTab] = useState(0);
  const [metrics, setMetrics] = useState<ModelPerformanceMetrics | null>(null);
  const [comparison, setComparison] = useState<ModelComparison | null>(null);
  const [templates, setTemplates] = useState<PromptTemplate[]>([]);
  const [fallbackConfig, setFallbackConfig] = useState<FallbackConfig | null>(null);
  const [newTemplate, setNewTemplate] = useState<Partial<PromptTemplate>>({});
  const { isOpen, onOpen, onClose } = useDisclosure();

  // Load providers
  useEffect(() => {
    const fetchProviders = async () => {
      try {
        const response = await fetch('http://localhost:8000/llm/providers');
        if (response.ok) {
          const data = await response.json();
          setProviders(data);
        }
      } catch (error) {
        console.error('Failed to fetch providers:', error);
      }
    };

    fetchProviders();
  }, []);

  // Load models when provider changes
  useEffect(() => {
    const fetchModels = async () => {
      if (!selectedProvider) return;

      try {
        const response = await fetch(
          `http://localhost:8000/llm/models/${selectedProvider}`
        );
        if (response.ok) {
          const data = await response.json();
          setModels(data);
        }
      } catch (error) {
        console.error('Failed to fetch models:', error);
      }
    };

    fetchModels();
  }, [selectedProvider]);

  // Load metrics when model changes
  useEffect(() => {
    const fetchMetrics = async () => {
      if (!config.model_name) return;
      
      try {
        const response = await fetch(
          `http://localhost:8000/llm/metrics/${config.model_name}`
        );
        if (response.ok) {
          const data = await response.json();
          setMetrics(data);
        }
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      }
    };

    fetchMetrics();
  }, [config.model_name]);

  // Load templates
  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const response = await fetch('http://localhost:8000/llm/templates');
        if (response.ok) {
          const data = await response.json();
          setTemplates(data);
        }
      } catch (error) {
        console.error('Failed to fetch templates:', error);
      }
    };

    fetchTemplates();
  }, []);

  // Load fallback config
  useEffect(() => {
    const fetchFallbackConfig = async () => {
      if (!config.model_name) return;
      
      try {
        const response = await fetch(
          `http://localhost:8000/llm/fallback/${config.model_name}`
        );
        if (response.ok) {
          const data = await response.json();
          setFallbackConfig(data);
        }
      } catch (error) {
        console.error('Failed to fetch fallback config:', error);
      }
    };

    fetchFallbackConfig();
  }, [config.model_name]);

  const handleProviderChange = (e: ChangeEvent<HTMLSelectElement>) => {
    const provider = e.target.value;
    setSelectedProvider(provider);
    setConfig((prev: LLMConfig) => ({
      ...prev,
      provider,
      model_name: '',
    }));
  };

  const handleInputChange = (e: InputChangeEvent) => {
    const { name, value } = e.target;
    setConfig((prev: LLMConfig) => ({ ...prev, [name]: value }));
  };

  const handleNumberChange = (name: string): NumberChangeHandler => {
    return (_, value) => {
      setConfig((prev: LLMConfig) => ({ ...prev, [name]: value }));
    };
  };

  const handleSwitchChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = e.target;
    setConfig((prev: LLMConfig) => ({ ...prev, [name]: checked }));
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/llm/configure', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) throw new Error('Failed to configure LLM');

      toast({
        title: 'LLM Configured',
        description: 'The LLM settings have been updated successfully.',
        status: 'success',
        duration: 5000,
      });
    } catch (error) {
      toast({
        title: 'Configuration Failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 5000,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCompareModels = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/llm/metrics/compare?${new URLSearchParams({
          model_names: models.map((m) => m.name).join(','),
        })}`
      );
      if (response.ok) {
        const data = await response.json();
        setComparison(data);
      }
    } catch (error) {
      console.error('Failed to compare models:', error);
    }
  };

  const handleCreateTemplate = async () => {
    try {
      const response = await fetch('http://localhost:8000/llm/templates', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newTemplate),
      });

      if (response.ok) {
        const data = await response.json();
        setTemplates([...templates, data]);
        setNewTemplate({});
        onClose();
        toast({
          title: 'Template Created',
          status: 'success',
          duration: 3000,
        });
      }
    } catch (error) {
      toast({
        title: 'Failed to create template',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const handleDeleteTemplate = async (id: string) => {
    try {
      const response = await fetch(`http://localhost:8000/llm/templates/${id}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setTemplates(templates.filter((t) => t.id !== id));
        toast({
          title: 'Template Deleted',
          status: 'success',
          duration: 3000,
        });
      }
    } catch (error) {
      toast({
        title: 'Failed to delete template',
        status: 'error',
        duration: 3000,
      });
    }
  };

  const handleUpdateFallback = async () => {
    if (!fallbackConfig) return;

    try {
      const response = await fetch('http://localhost:8000/llm/fallback/configure', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(fallbackConfig),
      });

      if (response.ok) {
        toast({
          title: 'Fallback Configuration Updated',
          status: 'success',
          duration: 3000,
        });
      }
    } catch (error) {
      toast({
        title: 'Failed to update fallback configuration',
        status: 'error',
        duration: 3000,
      });
    }
  };

  return (
    <Card>
      <CardBody>
        <Tabs index={activeTab} onChange={setActiveTab}>
          <TabList>
            <Tab>Configuration</Tab>
            <Tab>Performance</Tab>
            <Tab>Templates</Tab>
            <Tab>Fallback</Tab>
          </TabList>

          <TabPanels>
            <TabPanel>
              <form onSubmit={handleSubmit}>
                <VStack spacing={6} align="stretch">
                  <Text fontSize="xl" fontWeight="bold">
                    LLM Configuration
                  </Text>

                  <FormControl isRequired>
                    <FormLabel>Provider</FormLabel>
                    <Select
                      value={selectedProvider}
                      onChange={handleProviderChange}
                      placeholder="Select LLM provider"
                    >
                      {providers.map((provider) => (
                        <option key={provider.id} value={provider.id}>
                          {provider.name}
                        </option>
                      ))}
                    </Select>
                  </FormControl>

                  {selectedProvider && (
                    <Box>
                      <FormLabel>Available Models</FormLabel>
                      <Table variant="simple" size="sm">
                        <Thead>
                          <Tr>
                            <Th>Model</Th>
                            <Th>Context</Th>
                            <Th>Capabilities</Th>
                            <Th>Pricing</Th>
                            <Th>Action</Th>
                          </Tr>
                        </Thead>
                        <Tbody>
                          {models.map((model) => (
                            <Tr key={model.name}>
                              <Td>{model.name}</Td>
                              <Td>{model.context_window.toLocaleString()} tokens</Td>
                              <Td>
                                <HStack spacing={2}>
                                  {model.capabilities.map((cap) => (
                                    <Badge key={cap} colorScheme="blue">
                                      {cap}
                                    </Badge>
                                  ))}
                                </HStack>
                              </Td>
                              <Td>{model.pricing || 'Free'}</Td>
                              <Td>
                                <Button
                                  size="sm"
                                  colorScheme={
                                    config.model_name === model.name ? 'green' : 'gray'
                                  }
                                  onClick={() =>
                                    setConfig((prev) => ({
                                      ...prev,
                                      model_name: model.name,
                                      context_window: model.context_window,
                                    }))
                                  }
                                >
                                  {config.model_name === model.name ? (
                                    <Icon as={FiCheck} />
                                  ) : (
                                    'Select'
                                  )}
                                </Button>
                              </Td>
                            </Tr>
                          ))}
                        </Tbody>
                      </Table>
                    </Box>
                  )}

                  {selectedProvider === 'ollama' && (
                    <FormControl>
                      <FormLabel>API Base URL</FormLabel>
                      <Input
                        value={config.api_base || ''}
                        onChange={(e) =>
                          setConfig((prev) => ({ ...prev, api_base: e.target.value }))
                        }
                        placeholder="http://localhost:11434"
                      />
                      <FormHelperText>
                        The base URL for your Ollama instance
                      </FormHelperText>
                    </FormControl>
                  )}

                  {selectedProvider !== 'ollama' && (
                    <FormControl isRequired>
                      <FormLabel>API Key</FormLabel>
                      <Input
                        type="password"
                        value={config.api_key || ''}
                        onChange={(e) =>
                          setConfig((prev) => ({ ...prev, api_key: e.target.value }))
                        }
                        placeholder="Enter your API key"
                      />
                    </FormControl>
                  )}

                  <FormControl>
                    <FormLabel>
                      Temperature{' '}
                      <Tooltip label="Controls randomness in responses. Higher values make the output more random, lower values make it more focused.">
                        <Icon as={FiInfo} />
                      </Tooltip>
                    </FormLabel>
                    <NumberInput
                      value={config.temperature}
                      onChange={(_, value) =>
                        setConfig((prev) => ({ ...prev, temperature: value }))
                      }
                      step={0.1}
                      min={0}
                      max={2}
                    >
                      <NumberInputField />
                      <NumberInputStepper>
                        <NumberIncrementStepper />
                        <NumberDecrementStepper />
                      </NumberInputStepper>
                    </NumberInput>
                  </FormControl>

                  <FormControl>
                    <FormLabel>
                      Max Tokens{' '}
                      <Tooltip label="Maximum number of tokens to generate. Leave empty for model default.">
                        <Icon as={FiInfo} />
                      </Tooltip>
                    </FormLabel>
                    <NumberInput
                      value={config.max_tokens || ''}
                      onChange={(_, value) =>
                        setConfig((prev) => ({ ...prev, max_tokens: value }))
                      }
                      min={1}
                      max={config.context_window || undefined}
                    >
                      <NumberInputField />
                      <NumberInputStepper>
                        <NumberIncrementStepper />
                        <NumberDecrementStepper />
                      </NumberInputStepper>
                    </NumberInput>
                  </FormControl>

                  <FormControl display="flex" alignItems="center">
                    <FormLabel mb="0">Enable Streaming</FormLabel>
                    <Switch
                      isChecked={config.streaming}
                      onChange={(e) =>
                        setConfig((prev) => ({
                          ...prev,
                          streaming: e.target.checked,
                        }))
                      }
                    />
                  </FormControl>

                  <Button
                    type="submit"
                    colorScheme="blue"
                    isLoading={isLoading}
                    isDisabled={!config.provider || !config.model_name}
                  >
                    Apply Configuration
                  </Button>
                </VStack>
              </form>
            </TabPanel>

            <TabPanel>
              <VStack spacing={6} align="stretch">
                <Text fontSize="xl" fontWeight="bold">
                  Model Performance Metrics
                </Text>

                {metrics && (
                  <SimpleGrid columns={2} spacing={4}>
                    <Stat>
                      <StatLabel>Average Latency</StatLabel>
                      <StatNumber>{metrics.average_latency.toFixed(2)}s</StatNumber>
                      <Progress value={Math.min(metrics.average_latency * 100, 100)} colorScheme="blue" />
                    </Stat>

                    <Stat>
                      <StatLabel>Token Throughput</StatLabel>
                      <StatNumber>{metrics.token_throughput.toFixed(2)} tokens/s</StatNumber>
                      <Progress value={Math.min(metrics.token_throughput, 100)} colorScheme="green" />
                    </Stat>

                    <Stat>
                      <StatLabel>Error Rate</StatLabel>
                      <StatNumber>{(metrics.error_rate * 100).toFixed(2)}%</StatNumber>
                      <Progress value={metrics.error_rate * 100} colorScheme="red" />
                    </Stat>

                    <Stat>
                      <StatLabel>Total Requests</StatLabel>
                      <StatNumber>{metrics.total_requests}</StatNumber>
                    </Stat>
                  </SimpleGrid>
                )}

                <Divider />

                <Box>
                  <HStack justify="space-between" mb={4}>
                    <Text fontSize="lg" fontWeight="semibold">
                      Token Usage
                    </Text>
                    <Button
                      leftIcon={<FiRefreshCw />}
                      size="sm"
                      onClick={handleCompareModels}
                    >
                      Compare Models
                    </Button>
                  </HStack>

                  {metrics?.total_tokens && (
                    <SimpleGrid columns={2} spacing={4}>
                      <Stat>
                        <StatLabel>Prompt Tokens</StatLabel>
                        <StatNumber>{metrics.total_tokens.prompt_tokens}</StatNumber>
                      </Stat>

                      <Stat>
                        <StatLabel>Completion Tokens</StatLabel>
                        <StatNumber>{metrics.total_tokens.completion_tokens}</StatNumber>
                      </Stat>

                      <Stat>
                        <StatLabel>Total Cost</StatLabel>
                        <StatNumber>${metrics.total_tokens.total_cost.toFixed(4)}</StatNumber>
                      </Stat>

                      <Stat>
                        <StatLabel>Cost per 1K Tokens</StatLabel>
                        <StatNumber>
                          $
                          {(
                            (metrics.total_tokens.total_cost * 1000) /
                            metrics.total_tokens.total_tokens
                          ).toFixed(4)}
                        </StatNumber>
                      </Stat>
                    </SimpleGrid>
                  )}

                  {comparison && (
                    <Box mt={6}>
                      <Text fontSize="lg" fontWeight="semibold" mb={4}>
                        Model Comparison
                      </Text>
                      <Table variant="simple" size="sm">
                        <Thead>
                          <Tr>
                            <Th>Model</Th>
                            <Th>Latency Score</Th>
                            <Th>Throughput Score</Th>
                            <Th>Reliability Score</Th>
                            <Th>Cost Efficiency</Th>
                          </Tr>
                        </Thead>
                        <Tbody>
                          {comparison.models.map((model) => (
                            <Tr key={model}>
                              <Td>{model}</Td>
                              <Td>
                                {comparison.benchmark_results[model].latency_score.toFixed(2)}
                              </Td>
                              <Td>
                                {comparison.benchmark_results[model].throughput_score.toFixed(2)}
                              </Td>
                              <Td>
                                {comparison.benchmark_results[model].reliability_score.toFixed(2)}
                              </Td>
                              <Td>
                                {comparison.benchmark_results[model].cost_efficiency.toFixed(2)}
                              </Td>
                            </Tr>
                          ))}
                        </Tbody>
                      </Table>
                    </Box>
                  )}
                </Box>
              </VStack>
            </TabPanel>

            <TabPanel>
              <VStack spacing={6} align="stretch">
                <HStack justify="space-between">
                  <Text fontSize="xl" fontWeight="bold">
                    Prompt Templates
                  </Text>
                  <Button leftIcon={<FiPlus />} onClick={onOpen}>
                    New Template
                  </Button>
                </HStack>

                <Accordion allowMultiple>
                  {templates.map((template) => (
                    <AccordionItem key={template.id}>
                      <h2>
                        <AccordionButton>
                          <Box flex="1" textAlign="left">
                            <HStack justify="space-between">
                              <Text fontWeight="semibold">{template.name}</Text>
                              <Badge colorScheme="blue">
                                {template.model_name}
                              </Badge>
                            </HStack>
                          </Box>
                          <AccordionIcon />
                        </AccordionButton>
                      </h2>
                      <AccordionPanel>
                        <VStack align="stretch" spacing={4}>
                          <Text color="gray.600">{template.description}</Text>
                          <Box bg="gray.50" p={4} borderRadius="md">
                            <pre>{template.template}</pre>
                          </Box>
                          <HStack>
                            <Text fontSize="sm" color="gray.500">
                              Variables:
                            </Text>
                            {template.variables.map((v) => (
                              <Badge key={v}>{v}</Badge>
                            ))}
                          </HStack>
                          <HStack justify="space-between">
                            <Text fontSize="sm" color="gray.500">
                              Used {template.usage_count} times
                            </Text>
                            <HStack>
                              <IconButton
                                aria-label="Edit template"
                                icon={<FiEdit2 />}
                                size="sm"
                                onClick={() => {
                                  setNewTemplate(template);
                                  onOpen();
                                }}
                              />
                              <IconButton
                                aria-label="Delete template"
                                icon={<FiTrash2 />}
                                size="sm"
                                colorScheme="red"
                                onClick={() => handleDeleteTemplate(template.id)}
                              />
                            </HStack>
                          </HStack>
                        </VStack>
                      </AccordionPanel>
                    </AccordionItem>
                  ))}
                </Accordion>
              </VStack>
            </TabPanel>

            <TabPanel>
              <VStack spacing={6} align="stretch">
                <Text fontSize="xl" fontWeight="bold">
                  Fallback Configuration
                </Text>

                {fallbackConfig && (
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      handleUpdateFallback();
                    }}
                  >
                    <VStack spacing={4} align="stretch">
                      <FormControl>
                        <FormLabel>Primary Model</FormLabel>
                        <Input
                          value={fallbackConfig.primary_model}
                          isReadOnly
                        />
                      </FormControl>

                      <FormControl>
                        <FormLabel>Fallback Models</FormLabel>
                        <Select
                          multiple
                          value={fallbackConfig.fallback_models}
                          onChange={(e) => {
                            const selected = Array.from(
                              e.target.selectedOptions,
                              (option) => option.value
                            );
                            setFallbackConfig({
                              ...fallbackConfig,
                              fallback_models: selected,
                            });
                          }}
                        >
                          {models
                            .filter((m) => m.name !== fallbackConfig.primary_model)
                            .map((model) => (
                              <option key={model.name} value={model.name}>
                                {model.name}
                              </option>
                            ))}
                        </Select>
                      </FormControl>

                      <FormControl>
                        <FormLabel>Max Retries</FormLabel>
                        <NumberInput
                          value={fallbackConfig.max_retries}
                          onChange={(_, value) =>
                            setFallbackConfig({
                              ...fallbackConfig,
                              max_retries: value,
                            })
                          }
                          min={1}
                          max={10}
                        >
                          <NumberInputField />
                          <NumberInputStepper>
                            <NumberIncrementStepper />
                            <NumberDecrementStepper />
                          </NumberInputStepper>
                        </NumberInput>
                      </FormControl>

                      <FormControl>
                        <FormLabel>Timeout (seconds)</FormLabel>
                        <NumberInput
                          value={fallbackConfig.timeout_seconds}
                          onChange={(_, value) =>
                            setFallbackConfig({
                              ...fallbackConfig,
                              timeout_seconds: value,
                            })
                          }
                          min={1}
                          max={120}
                        >
                          <NumberInputField />
                          <NumberInputStepper>
                            <NumberIncrementStepper />
                            <NumberDecrementStepper />
                          </NumberInputStepper>
                        </NumberInput>
                      </FormControl>

                      <Button type="submit" colorScheme="blue">
                        Update Fallback Configuration
                      </Button>
                    </VStack>
                  </form>
                )}
              </VStack>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </CardBody>

      {/* Template Modal */}
      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            {newTemplate.id ? 'Edit Template' : 'New Template'}
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Name</FormLabel>
                <Input
                  value={newTemplate.name || ''}
                  onChange={(e) =>
                    setNewTemplate({ ...newTemplate, name: e.target.value })
                  }
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel>Description</FormLabel>
                <Textarea
                  value={newTemplate.description || ''}
                  onChange={(e) =>
                    setNewTemplate({
                      ...newTemplate,
                      description: e.target.value,
                    })
                  }
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel>Template</FormLabel>
                <Textarea
                  value={newTemplate.template || ''}
                  onChange={(e) =>
                    setNewTemplate({
                      ...newTemplate,
                      template: e.target.value,
                    })
                  }
                  height="200px"
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel>Variables (comma-separated)</FormLabel>
                <Input
                  value={newTemplate.variables?.join(', ') || ''}
                  onChange={(e) =>
                    setNewTemplate({
                      ...newTemplate,
                      variables: e.target.value
                        .split(',')
                        .map((v) => v.trim())
                        .filter(Boolean),
                    })
                  }
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel>Model</FormLabel>
                <Select
                  value={newTemplate.model_name || ''}
                  onChange={(e) =>
                    setNewTemplate({
                      ...newTemplate,
                      model_name: e.target.value,
                    })
                  }
                >
                  <option value="">Select a model</option>
                  {models.map((model) => (
                    <option key={model.name} value={model.name}>
                      {model.name}
                    </option>
                  ))}
                </Select>
              </FormControl>

              <FormControl>
                <FormLabel>Temperature</FormLabel>
                <NumberInput
                  value={newTemplate.temperature || 0.7}
                  onChange={(_, value) =>
                    setNewTemplate({
                      ...newTemplate,
                      temperature: value,
                    })
                  }
                  step={0.1}
                  min={0}
                  max={2}
                >
                  <NumberInputField />
                  <NumberInputStepper>
                    <NumberIncrementStepper />
                    <NumberDecrementStepper />
                  </NumberInputStepper>
                </NumberInput>
              </FormControl>

              <FormControl>
                <FormLabel>Max Tokens</FormLabel>
                <NumberInput
                  value={newTemplate.max_tokens || ''}
                  onChange={(_, value) =>
                    setNewTemplate({
                      ...newTemplate,
                      max_tokens: value,
                    })
                  }
                  min={1}
                >
                  <NumberInputField />
                  <NumberInputStepper>
                    <NumberIncrementStepper />
                    <NumberDecrementStepper />
                  </NumberInputStepper>
                </NumberInput>
              </FormControl>
            </VStack>
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button colorScheme="blue" onClick={handleCreateTemplate}>
              {newTemplate.id ? 'Update' : 'Create'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Card>
  );
};

export default LLMConfig; 