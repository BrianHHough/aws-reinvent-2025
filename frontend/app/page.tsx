"use client"

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, DollarSign, Users, Activity, Menu, X } from 'lucide-react';
import { HomepageProps, NavbarProps } from '@/types/HomepageTypes';
import Link from 'next/link';
import dynamic from 'next/dynamic';


const StreamChatWidget = dynamic(
  () => import('@/components/chat/StreamChatWidget'),
  { ssr: false } // ⬅️ important for browser-only libs
);


// Sample data for charts
const revenueData = [
  { month: 'Jan', revenue: 45000, expenses: 32000 },
  { month: 'Feb', revenue: 52000, expenses: 35000 },
  { month: 'Mar', revenue: 48000, expenses: 33000 },
  { month: 'Apr', revenue: 61000, expenses: 38000 },
  { month: 'May', revenue: 55000, expenses: 36000 },
  { month: 'Jun', revenue: 67000, expenses: 40000 },
];

const portfolioData = [
  { name: 'Stocks', value: 45 },
  { name: 'Bonds', value: 25 },
  { name: 'Real Estate', value: 20 },
  { name: 'Cash', value: 10 },
];

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

const Navbar = ({ onLoginClick, isLoggedIn }: NavbarProps) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <div className="flex items-center">
            <div className="shrink-0 flex items-center">
              <TrendingUp className="h-8 w-8 text-blue-600" />
              <span className="ml-2 text-2xl font-bold text-gray-900">FinStack</span>
            </div>
            <div className="hidden md:ml-10 md:flex md:space-x-8">
              <a href="#features" className="text-gray-700 hover:text-blue-600 px-3 py-2 text-sm font-medium transition">
                Features
              </a>
              <a href="#solutions" className="text-gray-700 hover:text-blue-600 px-3 py-2 text-sm font-medium transition">
                Solutions
              </a>
              <a href="#pricing" className="text-gray-700 hover:text-blue-600 px-3 py-2 text-sm font-medium transition">
                Pricing
              </a>
              <a href="#about" className="text-gray-700 hover:text-blue-600 px-3 py-2 text-sm font-medium transition">
                About
              </a>
            </div>
          </div>
          <div className="hidden md:flex items-center space-x-4">
            {!isLoggedIn ? (
              <Button onClick={onLoginClick} className="bg-blue-600 hover:bg-blue-700">
                Login
              </Button>
            ) : (
              <Link href="/">
                <Button className="bg-blue-600 hover:bg-blue-700">
                  My Account
                </Button>
              </Link>
            )}
          </div>
          <div className="md:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="text-gray-700 hover:text-blue-600"
            >
              {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>
      </div>
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-gray-200">
          <div className="px-2 pt-2 pb-3 space-y-1">
            <a href="#features" className="block px-3 py-2 text-gray-700 hover:bg-gray-50 rounded-md">
              Features
            </a>
            <a href="#solutions" className="block px-3 py-2 text-gray-700 hover:bg-gray-50 rounded-md">
              Solutions
            </a>
            <a href="#pricing" className="block px-3 py-2 text-gray-700 hover:bg-gray-50 rounded-md">
              Pricing
            </a>
            <a href="#about" className="block px-3 py-2 text-gray-700 hover:bg-gray-50 rounded-md">
              About
            </a>
            {!isLoggedIn && (
              <Button onClick={onLoginClick} className="w-full mt-4 bg-blue-600 hover:bg-blue-700">
                Login
              </Button>
            )}
            {isLoggedIn && (
              <Link
                href="/"
                className=""
              >
                <Button className="w-full mt-4 bg-blue-600 hover:bg-blue-700">
                  My Account
                </Button>
              </Link>
            )}
          </div>
        </div>
      )}
    </nav>
  );
};

const Homepage = ({ onLoginClick }: HomepageProps) => {
  return (
    <div className="min-h-screen bg-linear-to-b from-gray-50 to-white">
      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
        <div className="text-center">
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
            Financial Intelligence,
            <span className="text-blue-600"> Simplified</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Real-time insights, powerful analytics, and seamless portfolio management — all in one platform built for modern finance teams.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button onClick={onLoginClick} size="lg" className="bg-blue-600 hover:bg-blue-700 text-lg px-8 py-6">
              Get Started
            </Button>
            <Button size="lg" variant="outline" className="text-lg px-8 py-6">
              Watch Demo
            </Button>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          Everything you need to manage your finances
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          <Card className="border-2 hover:border-blue-500 transition">
            <CardHeader>
              <Activity className="h-12 w-12 text-blue-600 mb-4" />
              <CardTitle>Real-Time Analytics</CardTitle>
              <CardDescription>
                Monitor your portfolio performance with live data and actionable insights
              </CardDescription>
            </CardHeader>
          </Card>
          <Card className="border-2 hover:border-blue-500 transition">
            <CardHeader>
              <DollarSign className="h-12 w-12 text-green-600 mb-4" />
              <CardTitle>Smart Forecasting</CardTitle>
              <CardDescription>
                AI-powered predictions help you make informed investment decisions
              </CardDescription>
            </CardHeader>
          </Card>
          <Card className="border-2 hover:border-blue-500 transition">
            <CardHeader>
              <Users className="h-12 w-12 text-purple-600 mb-4" />
              <CardTitle>Team Collaboration</CardTitle>
              <CardDescription>
                Work seamlessly with your team on financial strategies and reporting
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-blue-600 py-16 mt-16">
        <div className="max-w-4xl mx-auto text-center px-4">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to transform your financial operations?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Join thousands of companies already using FinStack
          </p>
          <Button onClick={onLoginClick} size="lg" variant="secondary" className="text-lg px-8 py-6">
            Start Free Trial
          </Button>
        </div>
      </div>
    </div>
  );
};

const Dashboard = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Financial Dashboard</h1>
          <p className="text-gray-600 mt-2">Welcome back — here&apos;s what&apos;s happening with your portfolio</p>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Total Revenue</CardTitle>
              <DollarSign className="h-4 w-4 text-gray-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">$328,000</div>
              <p className="text-xs text-green-600 flex items-center mt-1">
                <TrendingUp className="h-3 w-3 mr-1" />
                +12.5% from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Portfolio Value</CardTitle>
              <Activity className="h-4 w-4 text-gray-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">$2.4M</div>
              <p className="text-xs text-green-600 flex items-center mt-1">
                <TrendingUp className="h-3 w-3 mr-1" />
                +8.3% this quarter
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Active Clients</CardTitle>
              <Users className="h-4 w-4 text-gray-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">1,284</div>
              <p className="text-xs text-green-600 flex items-center mt-1">
                <TrendingUp className="h-3 w-3 mr-1" />
                +23 new this week
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Monthly Growth</CardTitle>
              <TrendingUp className="h-4 w-4 text-gray-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">18.2%</div>
              <p className="text-xs text-green-600 flex items-center mt-1">
                <TrendingUp className="h-3 w-3 mr-1" />
                Above target by 3.2%
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <Card>
            <CardHeader>
              <CardTitle>Revenue vs Expenses</CardTitle>
              <CardDescription>6-month financial performance overview</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={revenueData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="revenue" stroke="#3b82f6" strokeWidth={2} />
                  <Line type="monotone" dataKey="expenses" stroke="#ef4444" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Portfolio Allocation</CardTitle>
              <CardDescription>Current asset distribution</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={portfolioData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => 
                      percent !== undefined ? `${name} ${(percent * 100).toFixed(0)}%` : name
                    }
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {portfolioData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Bar Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Monthly Performance</CardTitle>
            <CardDescription>Revenue and expense trends over the last 6 months</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={revenueData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="revenue" fill="#3b82f6" />
                <Bar dataKey="expenses" fill="#ef4444" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default function FintechApp() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const handleLogin = () => {
    setIsLoggedIn(true);
  };

  return (
    <div className="min-h-screen">
      <Navbar onLoginClick={handleLogin} isLoggedIn={isLoggedIn} />
      {isLoggedIn ? <Dashboard /> : <Homepage onLoginClick={handleLogin} />}
      
      {/* Floating chat widget in bottom-right */}
      <div className="fixed bottom-4 right-4 z-50 w-full max-w-sm">
        <StreamChatWidget />
      </div>
    </div>
  );
}