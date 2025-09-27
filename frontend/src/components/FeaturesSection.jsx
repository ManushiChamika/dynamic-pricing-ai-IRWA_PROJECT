import { FiCpu, FiTool, FiSliders, FiServer } from 'react-icons/fi';

const FeaturesSection = () => {
  const features = [
    {
      icon: <FiCpu className="w-8 h-8" />,
      title: "Custom PC Builds",
      description: "We design and build high-performance custom PCs tailored to your needs, whether you're a gamer, developer, or content creator."
    },
    {
      icon: <FiTool className="w-8 h-8" />,
      title: "PC Repair & Service",
      description: "Our expert technicians provide comprehensive repair and maintenance services for all types of PCs, from hardware upgrades to troubleshooting."
    },
    {
      icon: <FiSliders className="w-8 h-8" />,
      title: "AI-Enhanced Services & Assistance",
      description: "From smart diagnostics to personalized system upgrades, we offer AI-driven services and AI assistance to optimize your PC’s performance and functionality."
    },
    {
      icon: <FiServer className="w-8 h-8" />,
      title: "Computer Sales & IT Solutions",
      description: "We offer a wide range of computers for sale, from desktops to laptops, along with IT solutions, hosting services, and cloud infrastructure to meet your business needs."
    }
  ];

  return (
    <div className='bg-primary'>
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-32">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12">
          {features.map((feature, index) => (
            <div key={index} className="flex flex-col text-white border-t border-white/20 pt-8">
              <div className="mb-4 text-white" aria-hidden="true">
                {feature.icon}
              </div>
              <h3 className="text-lg font-medium mb-2">{feature.title}</h3>
              <p className="text-gray-500 mb-4 flex-1">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default FeaturesSection;
