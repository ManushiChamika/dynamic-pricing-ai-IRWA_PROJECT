import React from 'react'

const TryNow = () => {
  return (
    <section className="bg-black text-white py-20">
      <div className="container mx-auto px-4">
        <div className="flex flex-col md:flex-row justify-between gap-16">
          <div className="md:w-3/5">
            <h1 className="text-4xl md:text-8xl font-bold mb-8">
              Try it for<br />free
            </h1>
            <p className="text-xl mb-8 md:max-w-lg">
              Try CodeTutor for as long as you like with our free Starter plan. Purchase a paid Site plan to publish, host, and unlock additional features.
            </p>
            <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-md transition-colors">
              Get started — it's free
            </button>
          </div>

          <div className="md:w-2/5 space-y-12">

            <div>
                <h2 className='md:text-xl text-lg leading-relaxed font-medium mb-4'>Try CodeTutor for as long as you like with our free Starter plan. Purchase a paid Site plan to publish, host, and unlock additional features.</h2>
            </div>


            <div>
              <h2 className="text-2xl font-bold mb-4">Contact sales</h2>
              <p className="text-gray-300 mb-4">
                Interested in CodeTutor Enterprise? Get in touch with our sales team to receive a free personalized demo.
              </p>
              <a href="#" className="inline-flex items-center text-white hover:underline">
                Contact sales <span className="ml-2">→</span>
              </a>
            </div>

            <div>
              <h2 className="text-2xl font-bold mb-4">Hire a Certified Partner</h2>
              <p className="text-gray-300 mb-4">
                Extend the power of your team by hiring a Certified CodeTutor Partner — we'll match you with the best in the business.
              </p>
              <a href="#" className="inline-flex items-center text-white hover:underline">
                Browse Partners <span className="ml-2">→</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default TryNow