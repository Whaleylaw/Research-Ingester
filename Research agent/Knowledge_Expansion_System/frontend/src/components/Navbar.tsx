import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Flex,
  Link,
  HStack,
  Icon,
  Text,
  useColorModeValue,
} from '@chakra-ui/react';
import {
  FiUpload,
  FiSearch,
  FiMessageSquare,
  FiShare2,
} from 'react-icons/fi';

const NavLink: React.FC<{
  to: string;
  icon: React.ElementType;
  children: React.ReactNode;
}> = ({ to, icon, children }) => (
  <Link
    as={RouterLink}
    to={to}
    px={4}
    py={2}
    rounded="md"
    _hover={{
      textDecoration: 'none',
      bg: useColorModeValue('gray.100', 'gray.700'),
    }}
    display="flex"
    alignItems="center"
  >
    <Icon as={icon} mr={2} />
    <Text>{children}</Text>
  </Link>
);

const Navbar: React.FC = () => {
  return (
    <Box bg={useColorModeValue('white', 'gray.800')} px={4} shadow="sm">
      <Flex h={16} alignItems="center" justifyContent="space-between">
        <Text
          fontSize="xl"
          fontWeight="bold"
          color={useColorModeValue('blue.600', 'blue.200')}
        >
          Knowledge Base
        </Text>

        <HStack spacing={4}>
          <NavLink to="/" icon={FiUpload}>
            Upload
          </NavLink>
          <NavLink to="/search" icon={FiSearch}>
            Search
          </NavLink>
          <NavLink to="/query" icon={FiMessageSquare}>
            Query
          </NavLink>
          <NavLink to="/graph" icon={FiShare2}>
            Graph
          </NavLink>
        </HStack>
      </Flex>
    </Box>
  );
};

export default Navbar; 