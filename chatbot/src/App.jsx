import React, { useState } from 'react';
import { Send, Plus } from 'lucide-react';
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { ScrollArea } from "../components/ui/scroll-area";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, BarElement } from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const ChatbotInterface = () => {
  // State for chat messages
  const [messages, setMessages] = useState([
    { role: 'bot', content: 'Hello! I can help you analyze your data. Type anything to start the analysis!' }
  ]);

  // State for visualization display
  const [showVisualizations, setShowVisualizations] = useState(false);
  const [isExpanding, setIsExpanding] = useState(false);

  // State for chart data
  const [chartData, setChartData] = useState({
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
    datasets: [
      {
        label: 'Sample Data',
        data: [400, 300, 600, 800, 550],
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.5)',
        tension: 0.1,
      },
    ],
  });

  // State for bar chart data
  const [barData, setBarData] = useState({
    labels: ['Category A', 'Category B', 'Category C', 'Category D'],
    datasets: [
      {
        label: 'Random Values',
        data: [65, 45, 73, 58],
        backgroundColor: [
          'rgba(255, 99, 132, 0.5)',
          'rgba(54, 162, 235, 0.5)',
          'rgba(255, 206, 86, 0.5)',
          'rgba(75, 192, 192, 0.5)',
        ],
        borderColor: [
          'rgba(255, 99, 132, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(75, 192, 192, 1)',
        ],
        borderWidth: 1,
      },
    ],
  });

  // State for table data
  const [tableData, setTableData] = useState([
    { id: 1, metric: 'Mean', value: 525 },
    { id: 2, metric: 'Median', value: 500 },
    { id: 3, metric: 'Std Dev', value: 212.13 }
  ]);

  // Function to generate random data
  const generateRandomData = () => {
    // Generate new line chart data
    const newLineData = {
      ...chartData,
      datasets: [{
        ...chartData.datasets[0],
        data: Array.from({ length: 5 }, () => Math.floor(Math.random() * 1000)),
      }]
    };

    // Generate new bar chart data
    const newBarData = {
      ...barData,
      datasets: [{
        ...barData.datasets[0],
        data: Array.from({ length: 4 }, () => Math.floor(Math.random() * 100)),
      }]
    };

    // Generate new statistics
    const newData = newLineData.datasets[0].data;
    const mean = newData.reduce((a, b) => a + b, 0) / newData.length;
    const sortedData = [...newData].sort((a, b) => a - b);
    const median = sortedData[Math.floor(sortedData.length / 2)];
    const stdDev = Math.sqrt(
      newData.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / newData.length
    );

    const newTableData = [
      { id: 1, metric: 'Mean', value: mean.toFixed(2) },
      { id: 2, metric: 'Median', value: median.toFixed(2) },
      { id: 3, metric: 'Std Dev', value: stdDev.toFixed(2) }
    ];

    setChartData(newLineData);
    setBarData(newBarData);
    setTableData(newTableData);
  };

  // Chart options configuration
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 750,
      easing: 'easeInOutQuart',
    },
    plugins: {
      legend: {
        position: 'top',
        labels: {
          boxWidth: 15,
          font: { size: 11 }
        }
      },
      title: {
        display: true,
        text: 'Data Analysis',
        font: { size: 13 }
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: { font: { size: 11 } }
      },
      x: {
        ticks: { font: { size: 11 } }
      }
    },
  };

  // Handle message submission
  const sendMessage = (e) => {
    e.preventDefault();
    const input = e.target.elements.messageInput;
    if (input.value.trim()) {
      setMessages([...messages, { role: 'user', content: input.value }]);
      
      // If it's the first message, trigger the expansion animation
      if (!showVisualizations) {
        setIsExpanding(true);
        setTimeout(() => {
          setShowVisualizations(true);
          setIsExpanding(false);
        }, 300);
      }

      generateRandomData();
      input.value = '';

      // Add bot response
      setTimeout(() => {
        setMessages(prev => [...prev, {
          role: 'bot',
          content: 'I\'ve analyzed your input and generated new visualizations!'
        }]);
      }, 500);
    }
  };

  return (
    <div className="flex min-h-screen bg-gray-50 p-4">
      <div 
        className={`mx-auto transition-all duration-300 ease-in-out ${
          isExpanding ? 'scale-95 opacity-90' : ''
        } ${
          showVisualizations ? 'w-full' : 'w-2/3 max-w-3xl'
        }`}
      >
        <div className={`flex gap-4 transition-all duration-300 ${
          showVisualizations ? 'opacity-100' : 'opacity-100'
        }`}>
          {/* Chat Interface */}
          <Card className={`border-2 rounded-xl shadow-sm flex flex-col transition-all duration-300 ${
            showVisualizations ? 'w-1/2' : 'w-full'
          }`}>
            <CardHeader className="border-b-2 bg-white rounded-t-xl py-3">
              <CardTitle>Data Analysis Assistant</CardTitle>
            </CardHeader>
            
            <CardContent className="flex-1 p-0">
              <ScrollArea className="h-[calc(100vh-180px)]">
                <div className="space-y-4 p-4">
                  {messages.map((message, index) => (
                    <div
                      key={index}
                      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[80%] rounded-xl p-3 shadow-sm ${
                          message.role === 'user'
                            ? 'bg-blue-500 text-white'
                            : 'bg-white border-2 border-gray-100'
                        }`}
                      >
                        {message.content}
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
            
            <CardFooter className="border-t-2 bg-white rounded-b-xl p-3">
              <form onSubmit={sendMessage} className="flex w-full gap-2">
                <Button variant="outline" size="icon" className="border-2">
                  <Plus className="h-4 w-4" />
                </Button>
                <Input
                  name="messageInput"
                  placeholder="Type anything to generate analysis..."
                  className="flex-1 border-2"
                />
                <Button type="submit" size="icon" className="border-2">
                  <Send className="h-4 w-4" />
                </Button>
              </form>
            </CardFooter>
          </Card>

          {/* Visualizations Panel */}
          {showVisualizations && (
            <div className="w-1/2 flex flex-col gap-3 transition-all duration-300">
              {/* Line Chart Card */}
              <Card className="border-2 rounded-xl shadow-sm flex-1">
                <CardHeader className="border-b-2 bg-white rounded-t-xl py-2">
                  <CardTitle className="text-sm">Trend Analysis</CardTitle>
                </CardHeader>
                <CardContent className="p-3">
                  <div className="h-[180px]">
                    <Line data={chartData} options={chartOptions} />
                  </div>
                </CardContent>
              </Card>

              {/* Bar Chart Card */}
              <Card className="border-2 rounded-xl shadow-sm flex-1">
                <CardHeader className="border-b-2 bg-white rounded-t-xl py-2">
                  <CardTitle className="text-sm">Category Distribution</CardTitle>
                </CardHeader>
                <CardContent className="p-3">
                  <div className="h-[180px]">
                    <Bar data={barData} options={chartOptions} />
                  </div>
                </CardContent>
              </Card>

              {/* Table Card */}
              <Card className="border-2 rounded-xl shadow-sm">
                <CardHeader className="border-b-2 bg-white rounded-t-xl py-2">
                  <CardTitle className="text-sm">Statistical Summary</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <div className="relative overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead className="bg-gray-50 border-b-2">
                        <tr>
                          <th className="p-2">Metric</th>
                          <th className="p-2">Value</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y-2">
                        {tableData.map((row) => (
                          <tr key={row.id} className="bg-white">
                            <td className="p-2 font-medium">{row.metric}</td>
                            <td className="p-2">{row.value}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatbotInterface;