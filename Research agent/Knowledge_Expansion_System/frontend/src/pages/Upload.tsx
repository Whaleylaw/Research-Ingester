import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  useToast,
  Text,
  Icon,
  Divider,
  Card,
  CardBody,
  Progress,
  Switch,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Link,
  Textarea,
  HStack,
  Tooltip,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  IconButton,
  TableContainer,
  Checkbox,
  Select,
  Stack,
  ButtonGroup,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  StatGroup,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Drawer,
  DrawerBody,
  DrawerHeader,
  DrawerOverlay,
  DrawerContent,
  DrawerCloseButton,
  useDisclosure,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  FormHelperText,
} from '@chakra-ui/react';
import {
  FiUpload,
  FiLink,
  FiCheck,
  FiX,
  FiAlertCircle,
  FiExternalLink,
  FiMoreVertical,
  FiDownload,
  FiPause,
  FiPlay,
  FiRefreshCw,
  FiFilter,
  FiSortDesc,
  FiSettings,
  FiClock,
  FiTrendingUp,
  FiAlertOctagon,
  FiActivity,
} from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';

interface UploadStatus {
  total_files: number;
  processed_files: number;
  failed_files: string[];
  nodes: Array<{
    id: string;
    title: string;
    source_type: string;
    summary: string;
    tags: string[];
    is_new_information: boolean;
    confidence_score: number;
  }>;
}

interface ScrapingStatus {
  job_id: string;
  total_urls: number;
  processed_urls: number;
  failed_urls: string[];
  nodes: Array<{
    id: string;
    title: string;
    source_type: string;
    summary: string;
    tags: string[];
    is_new_information: boolean;
    confidence_score: number;
  }>;
  is_complete: boolean;
}

interface BatchJobStatus extends UploadStatus {
  job_id: string;
  status: 'running' | 'paused' | 'completed' | 'cancelled';
  progress_details: Record<string, any>;
  started_at: string;
  updated_at: string;
}

interface BatchMetrics {
  processing_speed: number;
  estimated_time_remaining: number;
  error_rate: number;
  success_rate: number;
  average_processing_time: number;
  elapsed_time: number;
}

interface BatchConfig {
  batch_size: number;
  error_threshold: number;
  auto_pause: boolean;
}

interface BatchAnalytics {
  total_processed: number;
  success_rate: number;
  average_processing_time: number;
  error_distribution: Record<string, number>;
  processing_speed_over_time: Array<Record<string, number>>;
  common_error_types: Array<{type: string; count: number}>;
}

const Upload: React.FC = () => {
  const [files, setFiles] = useState<FileList | null>(null);
  const [urls, setUrls] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus | null>(null);
  const [scrapingStatus, setScrapingStatus] = useState<ScrapingStatus | null>(null);
  const [followLinks, setFollowLinks] = useState(false);
  const [maxDepth, setMaxDepth] = useState(1);
  const [sameDomain, setSameDomain] = useState(true);
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [sortField, setSortField] = useState<string>('title');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const toast = useToast();
  const navigate = useNavigate();
  const [batchConfig, setBatchConfig] = useState<BatchConfig>({
    batch_size: 10,
    error_threshold: 0.2,
    auto_pause: true,
  });
  const [metrics, setMetrics] = useState<BatchMetrics | null>(null);
  const [analytics, setAnalytics] = useState<BatchAnalytics | null>(null);
  const [jobHistory, setJobHistory] = useState<Array<any>>([]);
  const { isOpen, onOpen, onClose } = useDisclosure();

  const handleBulkUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!files?.length) return;

    setIsLoading(true);
    try {
      const formData = new FormData();
      Array.from(files).forEach((file) => {
        formData.append('files', file);
      });

      const response = await fetch('http://localhost:8000/upload/bulk', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Upload failed');

      const data = await response.json();
      setUploadStatus(data);

      toast({
        title: 'Upload successful',
        description: `Processed ${data.processed_files} of ${data.total_files} files`,
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: 'Upload failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleWebScraping = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urls.trim()) return;

    setIsLoading(true);
    try {
      // Start scraping job
      const response = await fetch('http://localhost:8000/scrape/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          urls: urls.split('\n').filter(Boolean),
          max_depth: maxDepth,
          follow_links: followLinks,
          same_domain_only: sameDomain,
        }),
      });

      if (!response.ok) throw new Error('Web scraping failed');

      const data = await response.json();
      setScrapingStatus(data);

      // Poll for status updates
      const pollInterval = setInterval(async () => {
        const statusResponse = await fetch(
          `http://localhost:8000/scrape/${data.job_id}`
        );
        if (statusResponse.ok) {
          const statusData = await statusResponse.json();
          setScrapingStatus(statusData);
          if (statusData.is_complete) {
            clearInterval(pollInterval);
            setIsLoading(false);
            toast({
              title: 'Web scraping complete',
              description: `Processed ${statusData.processed_urls} URLs`,
              status: 'success',
              duration: 5000,
              isClosable: true,
            });
          }
        }
      }, 2000);
    } catch (error) {
      toast({
        title: 'Web scraping failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
      setIsLoading(false);
    }
  };

  const handleBatchControl = async (action: string) => {
    if (!uploadStatus?.job_id) return;

    try {
      const response = await fetch('http://localhost:8000/batch/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: uploadStatus.job_id,
          action,
        }),
      });

      if (!response.ok) throw new Error('Failed to control batch job');

      const data = await response.json();
      setUploadStatus(data);

      toast({
        title: `Batch job ${action}ed`,
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: `Failed to ${action} batch job`,
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 5000,
      });
    }
  };

  const handleRetry = async () => {
    if (!uploadStatus?.job_id || selectedItems.size === 0) return;

    try {
      const response = await fetch('http://localhost:8000/batch/retry', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: uploadStatus.job_id,
          items: Array.from(selectedItems),
        }),
      });

      if (!response.ok) throw new Error('Failed to retry items');

      const data = await response.json();
      setUploadStatus(data);
      setSelectedItems(new Set());

      toast({
        title: 'Retrying selected items',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Failed to retry items',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 5000,
      });
    }
  };

  const handleExport = async (format: 'json' | 'csv') => {
    if (!uploadStatus?.job_id) return;

    try {
      const response = await fetch(
        `http://localhost:8000/batch/export/${uploadStatus.job_id}?format=${format}`
      );

      if (!response.ok) throw new Error('Failed to export results');

      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `batch_job_${uploadStatus.job_id}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: 'Export successful',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Export failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 5000,
      });
    }
  };

  const sortedAndFilteredNodes = useMemo(() => {
    if (!uploadStatus) return [];

    let nodes = [...uploadStatus.nodes];
    
    // Apply filtering
    if (filterStatus !== 'all') {
      nodes = nodes.filter(node => 
        filterStatus === 'new' ? node.is_new_information : !node.is_new_information
      );
    }

    // Apply sorting
    nodes.sort((a, b) => {
      const aValue = a[sortField as keyof typeof a];
      const bValue = b[sortField as keyof typeof b];
      const comparison = aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return nodes;
  }, [uploadStatus, sortField, sortOrder, filterStatus]);

  // Add polling for metrics
  useEffect(() => {
    if (!uploadStatus?.job_id || uploadStatus.status === 'completed') return;

    const interval = setInterval(async () => {
      try {
        const [metricsRes, analyticsRes] = await Promise.all([
          fetch(`http://localhost:8000/batch/metrics/${uploadStatus.job_id}`),
          fetch('http://localhost:8000/batch/analytics'),
        ]);

        if (metricsRes.ok) {
          const metricsData = await metricsRes.json();
          setMetrics(metricsData);
        }

        if (analyticsRes.ok) {
          const analyticsData = await analyticsRes.json();
          setAnalytics(analyticsData);
        }
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [uploadStatus?.job_id, uploadStatus?.status]);

  // Load job history
  const loadJobHistory = async () => {
    try {
      const response = await fetch('http://localhost:8000/batch/history');
      if (response.ok) {
        const data = await response.json();
        setJobHistory(data.items);
      }
    } catch (error) {
      console.error('Failed to load job history:', error);
    }
  };

  // Configure batch processing
  const handleConfigureJob = async () => {
    if (!uploadStatus?.job_id) return;

    try {
      const response = await fetch(
        `http://localhost:8000/batch/configure/${uploadStatus.job_id}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(batchConfig),
        }
      );

      if (!response.ok) throw new Error('Failed to configure job');

      toast({
        title: 'Configuration updated',
        status: 'success',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: 'Failed to update configuration',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 5000,
      });
    }
  };

  // Format time duration
  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };

  return (
    <VStack spacing={8} align="stretch">
      <Text fontSize="2xl" fontWeight="bold">
        Add Content to Knowledge Base
      </Text>

      <Card>
        <CardBody>
          <form onSubmit={handleBulkUpload}>
            <VStack spacing={4} align="stretch">
              <Text fontSize="lg" fontWeight="semibold">
                Bulk File Upload
              </Text>
              <Text color="gray.600">
                Upload multiple files at once (PDF, video, audio, documents)
              </Text>
              <FormControl>
                <FormLabel>Select Files</FormLabel>
                <Input
                  type="file"
                  onChange={(e) => setFiles(e.target.files)}
                  accept=".pdf,.mp4,.mp3,.wav,.doc,.docx"
                  multiple
                />
              </FormControl>
              <Button
                type="submit"
                colorScheme="blue"
                leftIcon={<Icon as={FiUpload} />}
                isLoading={isLoading}
                loadingText="Uploading"
                isDisabled={!files?.length}
              >
                Upload Files
              </Button>

              {uploadStatus && (
                <Box>
                  <Stack direction="row" justify="space-between" mb={4}>
                    <ButtonGroup size="sm">
                      <Button
                        leftIcon={<Icon as={uploadStatus.status === 'running' ? FiPause : FiPlay} />}
                        onClick={() => handleBatchControl(uploadStatus.status === 'running' ? 'pause' : 'resume')}
                        isDisabled={uploadStatus.status === 'completed' || uploadStatus.status === 'cancelled'}
                      >
                        {uploadStatus.status === 'running' ? 'Pause' : 'Resume'}
                      </Button>
                      <Button
                        leftIcon={<Icon as={FiX} />}
                        onClick={() => handleBatchControl('cancel')}
                        isDisabled={uploadStatus.status === 'completed' || uploadStatus.status === 'cancelled'}
                      >
                        Cancel
                      </Button>
                      <Button
                        leftIcon={<Icon as={FiRefreshCw} />}
                        onClick={handleRetry}
                        isDisabled={selectedItems.size === 0}
                      >
                        Retry Selected
                      </Button>
                    </ButtonGroup>

                    <Stack direction="row" spacing={4}>
                      <Select
                        size="sm"
                        value={filterStatus}
                        onChange={(e) => setFilterStatus(e.target.value)}
                        w="150px"
                      >
                        <option value="all">All Status</option>
                        <option value="new">New Information</option>
                        <option value="existing">Existing Information</option>
                      </Select>

                      <Select
                        size="sm"
                        value={sortField}
                        onChange={(e) => setSortField(e.target.value)}
                        w="150px"
                      >
                        <option value="title">Sort by Title</option>
                        <option value="source_type">Sort by Type</option>
                        <option value="confidence_score">Sort by Confidence</option>
                      </Select>

                      <IconButton
                        aria-label="Toggle sort order"
                        icon={<Icon as={FiSortDesc} />}
                        size="sm"
                        onClick={() => setSortOrder(order => order === 'asc' ? 'desc' : 'asc')}
                      />

                      <Menu>
                        <MenuButton
                          as={IconButton}
                          icon={<Icon as={FiMoreVertical} />}
                          variant="ghost"
                          size="sm"
                        />
                        <MenuList>
                          <MenuItem icon={<Icon as={FiDownload} />} onClick={() => handleExport('json')}>
                            Export as JSON
                          </MenuItem>
                          <MenuItem icon={<Icon as={FiDownload} />} onClick={() => handleExport('csv')}>
                            Export as CSV
                          </MenuItem>
                        </MenuList>
                      </Menu>
                    </Stack>
                  </Stack>

                  <Progress
                    value={(uploadStatus.processed_files / uploadStatus.total_files) * 100}
                    size="sm"
                    mb={4}
                    hasStripe={uploadStatus.status === 'running'}
                    isAnimated={uploadStatus.status === 'running'}
                  />

                  <TableContainer>
                    <Table variant="simple" size="sm">
                      <Thead>
                        <Tr>
                          <Th width="40px">
                            <Checkbox
                              isChecked={selectedItems.size > 0 && selectedItems.size === uploadStatus.failed_files.length}
                              isIndeterminate={selectedItems.size > 0 && selectedItems.size < uploadStatus.failed_files.length}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedItems(new Set(uploadStatus.failed_files));
                                } else {
                                  setSelectedItems(new Set());
                                }
                              }}
                            />
                          </Th>
                          <Th>Title</Th>
                          <Th>Type</Th>
                          <Th>Status</Th>
                          <Th>Actions</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {sortedAndFilteredNodes.map((node) => (
                          <Tr key={node.id}>
                            <Td>
                              <Checkbox
                                isChecked={selectedItems.has(node.id)}
                                onChange={(e) => {
                                  const newSelected = new Set(selectedItems);
                                  if (e.target.checked) {
                                    newSelected.add(node.id);
                                  } else {
                                    newSelected.delete(node.id);
                                  }
                                  setSelectedItems(newSelected);
                                }}
                              />
                            </Td>
                            <Td>{node.title}</Td>
                            <Td>
                              <Badge colorScheme="purple">{node.source_type}</Badge>
                            </Td>
                            <Td>
                              <Badge
                                colorScheme={node.is_new_information ? 'green' : 'blue'}
                              >
                                {node.is_new_information ? 'New' : 'Existing'}
                              </Badge>
                            </Td>
                            <Td>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => navigate(`/nodes/${node.id}`)}
                              >
                                View
                              </Button>
                            </Td>
                          </Tr>
                        ))}
                      </Tbody>
                    </Table>
                  </TableContainer>
                </Box>
              )}
            </VStack>
          </form>
        </CardBody>
      </Card>

      <Divider />

      <Card>
        <CardBody>
          <form onSubmit={handleWebScraping}>
            <VStack spacing={4} align="stretch">
              <Text fontSize="lg" fontWeight="semibold">
                Web Scraping
              </Text>
              <Text color="gray.600">
                Process multiple web pages and their linked content
              </Text>

              <FormControl>
                <FormLabel>URLs (one per line)</FormLabel>
                <Textarea
                  value={urls}
                  onChange={(e) => setUrls(e.target.value)}
                  placeholder="https://example.com/article1&#10;https://example.com/article2"
                  rows={5}
                />
              </FormControl>

              <FormControl display="flex" alignItems="center">
                <FormLabel mb="0">Follow Links</FormLabel>
                <Switch
                  isChecked={followLinks}
                  onChange={(e) => setFollowLinks(e.target.checked)}
                />
              </FormControl>

              {followLinks && (
                <>
                  <FormControl>
                    <FormLabel>Maximum Depth</FormLabel>
                    <NumberInput
                      value={maxDepth}
                      onChange={(_, value) => setMaxDepth(value)}
                      min={1}
                      max={5}
                    >
                      <NumberInputField />
                      <NumberInputStepper>
                        <NumberIncrementStepper />
                        <NumberDecrementStepper />
                      </NumberInputStepper>
                    </NumberInput>
                  </FormControl>

                  <FormControl display="flex" alignItems="center">
                    <FormLabel mb="0">Same Domain Only</FormLabel>
                    <Switch
                      isChecked={sameDomain}
                      onChange={(e) => setSameDomain(e.target.checked)}
                    />
                  </FormControl>
                </>
              )}

              <Button
                type="submit"
                colorScheme="blue"
                leftIcon={<Icon as={FiLink} />}
                isLoading={isLoading}
                loadingText="Processing"
                isDisabled={!urls.trim()}
              >
                Start Scraping
              </Button>

              {scrapingStatus && (
                <Box>
                  <Progress
                    value={
                      (scrapingStatus.processed_urls / scrapingStatus.total_urls) * 100
                    }
                    size="sm"
                    mb={4}
                  />
                  <Table variant="simple" size="sm">
                    <Thead>
                      <Tr>
                        <Th>Title</Th>
                        <Th>Type</Th>
                        <Th>Status</Th>
                        <Th>Actions</Th>
                      </Tr>
                    </Thead>
                    <Tbody>
                      {scrapingStatus.nodes.map((node) => (
                        <Tr key={node.id}>
                          <Td>{node.title}</Td>
                          <Td>
                            <Badge colorScheme="purple">{node.source_type}</Badge>
                          </Td>
                          <Td>
                            <Badge
                              colorScheme={node.is_new_information ? 'green' : 'blue'}
                            >
                              {node.is_new_information ? 'New' : 'Existing'}
                            </Badge>
                          </Td>
                          <Td>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => navigate(`/nodes/${node.id}`)}
                            >
                              View
                            </Button>
                          </Td>
                        </Tr>
                      ))}
                      {scrapingStatus.failed_urls.map((failure) => (
                        <Tr key={failure}>
                          <Td colSpan={4}>
                            <HStack color="red.500">
                              <Icon as={FiX} />
                              <Text>{failure}</Text>
                            </HStack>
                          </Td>
                        </Tr>
                      ))}
                    </Tbody>
                  </Table>
                </Box>
              )}
            </VStack>
          </form>
        </CardBody>
      </Card>

      {uploadStatus && (
        <Box>
          <Stack direction="row" justify="space-between" mb={4}>
            <ButtonGroup>
              <IconButton
                aria-label="Configure batch processing"
                icon={<Icon as={FiSettings} />}
                onClick={onOpen}
              />
              <IconButton
                aria-label="View job history"
                icon={<Icon as={FiClock} />}
                onClick={loadJobHistory}
              />
            </ButtonGroup>
          </Stack>

          {metrics && (
            <StatGroup mb={4}>
              <Stat>
                <StatLabel>Processing Speed</StatLabel>
                <StatNumber>{metrics.processing_speed.toFixed(2)}/s</StatNumber>
                <StatHelpText>
                  <StatArrow type="increase" />
                  Items processed per second
                </StatHelpText>
              </Stat>

              <Stat>
                <StatLabel>Time Remaining</StatLabel>
                <StatNumber>
                  {formatDuration(metrics.estimated_time_remaining)}
                </StatNumber>
                <StatHelpText>
                  Elapsed: {formatDuration(metrics.elapsed_time)}
                </StatHelpText>
              </Stat>

              <Stat>
                <StatLabel>Success Rate</StatLabel>
                <StatNumber>
                  {(metrics.success_rate * 100).toFixed(1)}%
                </StatNumber>
                <StatHelpText>
                  Error Rate: {(metrics.error_rate * 100).toFixed(1)}%
                </StatHelpText>
              </Stat>
            </StatGroup>
          )}

          <TableContainer>
            <Table variant="simple" size="sm">
              <Thead>
                <Tr>
                  <Th width="40px">
                    <Checkbox
                      isChecked={selectedItems.size > 0 && selectedItems.size === uploadStatus.failed_files.length}
                      isIndeterminate={selectedItems.size > 0 && selectedItems.size < uploadStatus.failed_files.length}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedItems(new Set(uploadStatus.failed_files));
                        } else {
                          setSelectedItems(new Set());
                        }
                      }}
                    />
                  </Th>
                  <Th>Title</Th>
                  <Th>Type</Th>
                  <Th>Status</Th>
                  <Th>Actions</Th>
                </Tr>
              </Thead>
              <Tbody>
                {sortedAndFilteredNodes.map((node) => (
                  <Tr key={node.id}>
                    <Td>
                      <Checkbox
                        isChecked={selectedItems.has(node.id)}
                        onChange={(e) => {
                          const newSelected = new Set(selectedItems);
                          if (e.target.checked) {
                            newSelected.add(node.id);
                          } else {
                            newSelected.delete(node.id);
                          }
                          setSelectedItems(newSelected);
                        }}
                      />
                    </Td>
                    <Td>{node.title}</Td>
                    <Td>
                      <Badge colorScheme="purple">{node.source_type}</Badge>
                    </Td>
                    <Td>
                      <Badge
                        colorScheme={node.is_new_information ? 'green' : 'blue'}
                      >
                        {node.is_new_information ? 'New' : 'Existing'}
                      </Badge>
                    </Td>
                    <Td>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => navigate(`/nodes/${node.id}`)}
                      >
                        View
                      </Button>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </TableContainer>
        </Box>
      )}

      {/* Batch Configuration Drawer */}
      <Drawer isOpen={isOpen} placement="right" onClose={onClose} size="md">
        <DrawerOverlay />
        <DrawerContent>
          <DrawerCloseButton />
          <DrawerHeader>Batch Processing Settings</DrawerHeader>

          <DrawerBody>
            <VStack spacing={6}>
              <FormControl>
                <FormLabel>Batch Size</FormLabel>
                <NumberInput
                  value={batchConfig.batch_size}
                  onChange={(_, value) =>
                    setBatchConfig((prev) => ({ ...prev, batch_size: value }))
                  }
                  min={1}
                  max={50}
                >
                  <NumberInputField />
                  <NumberInputStepper>
                    <NumberIncrementStepper />
                    <NumberDecrementStepper />
                  </NumberInputStepper>
                </NumberInput>
                <FormHelperText>
                  Number of items to process concurrently
                </FormHelperText>
              </FormControl>

              <FormControl>
                <FormLabel>Error Threshold</FormLabel>
                <NumberInput
                  value={batchConfig.error_threshold}
                  onChange={(_, value) =>
                    setBatchConfig((prev) => ({ ...prev, error_threshold: value }))
                  }
                  min={0}
                  max={1}
                  step={0.05}
                >
                  <NumberInputField />
                  <NumberInputStepper>
                    <NumberIncrementStepper />
                    <NumberDecrementStepper />
                  </NumberInputStepper>
                </NumberInput>
                <FormHelperText>
                  Auto-pause when error rate exceeds this threshold
                </FormHelperText>
              </FormControl>

              <FormControl display="flex" alignItems="center">
                <FormLabel mb="0">Auto-Pause on Errors</FormLabel>
                <Switch
                  isChecked={batchConfig.auto_pause}
                  onChange={(e) =>
                    setBatchConfig((prev) => ({
                      ...prev,
                      auto_pause: e.target.checked,
                    }))
                  }
                />
              </FormControl>

              <Button
                colorScheme="blue"
                onClick={handleConfigureJob}
                isDisabled={!uploadStatus?.job_id}
              >
                Apply Configuration
              </Button>

              {analytics && (
                <Accordion allowMultiple w="100%">
                  <AccordionItem>
                    <AccordionButton>
                      <Box flex="1" textAlign="left">
                        Processing Analytics
                      </Box>
                      <AccordionIcon />
                    </AccordionButton>
                    <AccordionPanel>
                      <VStack align="stretch" spacing={4}>
                        <Stat>
                          <StatLabel>Total Processed</StatLabel>
                          <StatNumber>{analytics.total_processed}</StatNumber>
                        </Stat>
                        <Stat>
                          <StatLabel>Overall Success Rate</StatLabel>
                          <StatNumber>
                            {(analytics.success_rate * 100).toFixed(1)}%
                          </StatNumber>
                        </Stat>
                        <Box>
                          <Text fontWeight="bold" mb={2}>
                            Common Error Types
                          </Text>
                          {analytics.common_error_types.map((error) => (
                            <HStack key={error.type} justify="space-between">
                              <Text>{error.type}</Text>
                              <Badge colorScheme="red">{error.count}</Badge>
                            </HStack>
                          ))}
                        </Box>
                      </VStack>
                    </AccordionPanel>
                  </AccordionItem>

                  <AccordionItem>
                    <AccordionButton>
                      <Box flex="1" textAlign="left">
                        Job History
                      </Box>
                      <AccordionIcon />
                    </AccordionButton>
                    <AccordionPanel>
                      <VStack align="stretch" spacing={4}>
                        {jobHistory.map((job) => (
                          <Card key={job.job_id} size="sm">
                            <CardBody>
                              <VStack align="stretch" spacing={2}>
                                <HStack justify="space-between">
                                  <Text fontWeight="bold">
                                    {job.job_type === 'upload'
                                      ? 'File Upload'
                                      : 'Web Scraping'}
                                  </Text>
                                  <Badge
                                    colorScheme={
                                      job.final_status === 'completed'
                                        ? 'green'
                                        : job.final_status === 'cancelled'
                                        ? 'red'
                                        : 'yellow'
                                    }
                                  >
                                    {job.final_status}
                                  </Badge>
                                </HStack>
                                <Text fontSize="sm" color="gray.600">
                                  Started: {new Date(job.start_time).toLocaleString()}
                                </Text>
                                <HStack justify="space-between">
                                  <Text fontSize="sm">
                                    Success Rate:{' '}
                                    {((job.successful_items / job.total_items) * 100).toFixed(1)}%
                                  </Text>
                                  <Text fontSize="sm">
                                    Duration: {formatDuration(job.duration)}
                                  </Text>
                                </HStack>
                              </VStack>
                            </CardBody>
                          </Card>
                        ))}
                      </VStack>
                    </AccordionPanel>
                  </AccordionItem>
                </Accordion>
              )}
            </VStack>
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </VStack>
  );
};

export default Upload; 