import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ChakraProvider, Box, Container } from '@chakra-ui/react';

import Navbar from './components/Navbar';
import Upload from './pages/Upload';
import Search from './pages/Search';
import Query from './pages/Query';
import Graph from './pages/Graph';
import NodeDetails from './pages/NodeDetails';

const App: React.FC = () => {
  return (
    <ChakraProvider>
      <Router>
        <Box minH="100vh" bg="gray.50">
          <Navbar />
          <Container maxW="container.xl" py={8}>
            <Routes>
              <Route path="/" element={<Upload />} />
              <Route path="/search" element={<Search />} />
              <Route path="/query" element={<Query />} />
              <Route path="/graph" element={<Graph />} />
              <Route path="/nodes/:nodeId" element={<NodeDetails />} />
            </Routes>
          </Container>
        </Box>
      </Router>
    </ChakraProvider>
  );
};

export default App; 