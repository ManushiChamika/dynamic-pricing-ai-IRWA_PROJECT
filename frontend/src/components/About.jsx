import React, { useEffect, useRef, useState } from "react";
import { HiArrowRight } from "react-icons/hi";

const features = [
  {
    id: "ai-1",
    title: "Generate styled content quickly",
    description:
      "Whether you're trying to build even faster or you're just new to codeTutor, you can use AI Assistant to generate new page sections using your site's existing design system.",
    link: "https://help.webflow.com/hc/en-us/articles/34205154436243",
    linkText: "Explore documentation",
    video:
      "https://dhygzobemt712.cloudfront.net/Web/home/2024-wxp/features/design-assistant-ai.mp4",
    poster:
      "https://cdn.prod.website-files.com/66e88746834b80507cdf7933/6705703132e8c6c85119c96d_design-assistant.avif",
  },
  {
    id: "ai-2",
    title: "Generate text right within codetutor",
    description:
      "Quickly and easily create new content, natively within CodeTutor. From generating first-pass content to publishing at speed, the AI Assistant can help you develop variations with just a few clicks.",
    link: "https://help.webflow.com/hc/articles/34295931022099",
    linkText: "Explore documentation",
    video:
      "https://dhygzobemt712.cloudfront.net/Web/home/2024-wxp/features/writing-assistant-square.mp4",
    poster:
      "https://cdn.prod.website-files.com/66e88746834b80507cdf7933/67057031236cd506cd0ae632_writing-assistant.avif",
  },
  {
    id: "ai-3",
    title: "Generate text right within CodeTutor",
    description:
      "Quickly and easily create new content, natively within codetutor. From generating first-pass content to publishing at speed, the AI Assistant can help you develop variations with just a few clicks.",
    link: "https://help.webflow.com/hc/articles/34295931022099",
    linkText: "Explore documentation",
    video:
      "https://dhygzobemt712.cloudfront.net/Web/home/2024-wxp/features/writing-assistant-square.mp4",
    poster:
      "https://cdn.prod.website-files.com/66e88746834b80507cdf7933/67057031236cd506cd0ae632_writing-assistant.avif",
  },
];

const About = () => {
  const [activeFeature, setActiveFeature] = useState(0);
  const featuresRef = useRef(null);
  const observerRef = useRef(null);

  useEffect(() => {
    const options = {
      root: null,
      rootMargin: "0px",
      threshold: 0.5,
    };

    observerRef.current = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const id = entry.target.getAttribute("id");
          const index = features.findIndex((feature) => feature.id === id);
          if (index !== -1) {
            setActiveFeature(index);
            const video = document.querySelector(`video[data-feature="${id}"]`);
            if (video) video.play();
          }
        }
      });
    }, options);

    const featureElements = document.querySelectorAll(".feature-item");
    featureElements.forEach((element) => {
      observerRef.current.observe(element);
    });

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, []);

  return (
    <section className="bg-black text-white py-24">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="grid grid-cols-1 lg:grid-cols-2 md:gap-32  gap-8">
          <div className="md:mb-24">
            <h2 className="text-5xl md:text-7xl font-bold mb-8 max-w-[50rem]">
              AI at Alpha IT Solution
            </h2>
          </div>
          <div className="mb-24">
            <p className="text-xl text-gray-300 mb-8 max-w-[35rem]">
            Alpha IT Solution integrates advanced AI features to deliver a smarter, more efficient, 
            and personalized experience for every user. From intelligent customer support to system 
            diagnostics and smart shopping tools, our AI services are designed to make your journey 
            smoother—whether you're browsing, building, or troubleshooting.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 md:gap-32 gap-8">
          {/* Left Column - Video */}
          <div>
            <div className="sticky top-24">
              <div className="aspect-square rounded-lg overflow-hidden border border-white/20">
                <video
                  key={features[activeFeature].id}
                  data-feature={features[activeFeature].id}
                  src={features[activeFeature].video}
                  poster={features[activeFeature].poster}
                  className="w-full h-full object-cover"
                  muted
                  playsInline
                  loop
                  autoPlay
                />
              </div>
            </div>
          </div>

          {/* Right Column - Features */}
          <div>
            {/* Intro Text */}
            <div className="md:mb-28 mb-16 md:h-72 border-b border-white/10 pb-16">
              <div className="max-w-[35ch] mb-4">
                <h3 className="text-2xl font-semibold">
                  TechNova Support
                </h3>
              </div>
              <p className="text-xl text-gray-300 mb-8 max-w-[35rem]">
              TechNova Support is an intelligent assistant available 24/7 to answer your 
              questions regarding store hours, product availability, PC configuration advice, 
              order status, and technical support. It ensures you receive quick and accurate 
              responses, enhancing your overall shopping experience.
              </p>
              <a
                href="/ContactUs"
                className="inline-flex items-center text-white hover:text-gray-300 text-lg font-medium transition-colors"
              >
                Chat with TechNova
                <HiArrowRight className="ml-2 w-5 h-5" />
              </a>
            </div>

            <div className="md:mb-28 mb-16 md:h-72 border-b border-white/10 pb-16">
              <div className="max-w-[35ch] mb-4">
                <h3 className="text-2xl font-semibold">
                  Smart Product Categorization
                </h3>
              </div>
              <p className="text-xl text-gray-300 mb-8 max-w-[35rem]">
                AI intelligently organizes products based on user behavior, trends, and specifications.
                Quickly find what you need without endless scrolling.
                Shopping becomes faster, smarter, and more personalized.
                Experience effortless product discovery powered by AI.
              </p>
              <a
                href="/AI-Engine"
                className="inline-flex items-center text-white hover:text-gray-300 text-lg font-medium transition-colors"
              >
                Browse Smarter
                <HiArrowRight className="ml-2 w-5 h-5" />
              </a>
            </div>
            <div className="md:mb-28 mb-16 md:h-72 border-b border-white/10 pb-16">
              <div className="max-w-[35ch] mb-4">
                <h3 className="text-2xl font-semibold">
                  Build Compatibility Checker
                </h3>
              </div>
              <p className="text-xl text-gray-300 mb-8 max-w-[35rem]">
                Our AI checker ensures all your selected PC parts are fully compatible.
                It prevents costly mistakes and boosts system performance.
                Customize your dream build with confidence and ease.
                AI guarantees a smooth and optimized setup every time.
              </p>
              <a
                href="/AI-build-suggestor"
                className="inline-flex items-center text-white hover:text-gray-300 text-lg font-medium transition-colors"
              >
                Try Build Compatibility Checker Now
                <HiArrowRight className="ml-2 w-5 h-5" />
              </a>
            </div>
            <div className="md:mb-28 mb-16 md:h-72 border-b border-white/10 pb-16">
              <div className="max-w-[35ch] mb-4">
                <h3 className="text-2xl font-semibold">
                  AI Computer Diagnosticians
                </h3>
              </div>
              <p className="text-xl text-gray-300 mb-8 max-w-[35rem]">
                Analyze, detect, and explain issues—powered by AI—based on your inputs, 
                then guide you toward solutions. Quickly pinpoint problems by reviewing 
                system logs, performance data, or error reports you provide. While it won't 
                auto-fix issues, it generates clear steps—so you can take action with confidence.  
              </p>
              <a
                href="/AppointmenentAI"
                className="inline-flex items-center text-white hover:text-gray-300 text-lg font-medium transition-colors"
              >
                Try AI Diagnostics Now 
                <HiArrowRight className="ml-2 w-5 h-5" />
              </a>
            </div>
            <div className="md:mb-28 mb-16 md:h-72 border-b border-white/10 pb-16">
              <div className="max-w-[35ch] mb-4">
                <h3 className="text-2xl font-semibold">
                  Order & Finance Intelligence
                </h3>
              </div>
              <p className="text-xl text-gray-300 mb-8 max-w-[35rem]">
                AI streamlines order management and financial operations effortlessly.
                It generates reports, detects fraud, and emails invoices automatically.
                Secure your transactions and enhance customer satisfaction.
                Smarter, safer, and faster — powered by intelligent automation.
              </p>
              <a
                href="/OrderSupportChat"
                className="inline-flex items-center text-white hover:text-gray-300 text-lg font-medium transition-colors"
              >
                Launch Finance AI
                <HiArrowRight className="ml-2 w-5 h-5" />
              </a>
            </div>

            {/* Features List *
            <div ref={featuresRef} className="space-y-24">
              {features.map((feature, index) => (
                <div
                  key={feature.id}
                  id={feature.id}
                  className="feature-item scroll-mt-24 md:h-72 border-b border-white/10 pb-16"
                >
                  <div className="max-w-[35ch] mb-4">
                    <h3 className="text-2xl font-semibold">{feature.title}</h3>
                  </div>
                  <p className="text-xl text-gray-300 mb-8 max-w-[35rem]">
                    {feature.description}
                  </p>
                  <a
                    href="https://webflow.com/ai"
                    className="inline-flex items-center text-white hover:text-gray-300 text-lg font-medium transition-colors"
                  >
                    Discover AI at CodeTutor
                    <HiArrowRight className="ml-2 w-5 h-5" />
                  </a>
                </div>
              ))}
            </div>
            */}
          </div>
        </div>
      </div>
    </section>
  );
};

export default About;
