const About = () => {
  return (
    <section id="about" className="py-24">
      <div className="container-fluid max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <div>
            <h2 className="text-fluid-xl font-light tracking-tight mb-8">
              We believe in the power of{' '}
              <span className="font-medium">simplicity</span>
            </h2>
            
            <div className="space-y-6 text-muted-foreground leading-relaxed">
              <p>
                Founded in 2020, our studio has been dedicated to creating 
                meaningful digital experiences that resonate with users and 
                drive business objectives.
              </p>
              
              <p>
                We work with a select group of clients, from ambitious startups 
                to established enterprises, helping them navigate the digital 
                landscape with confidence and clarity.
              </p>
              
              <p>
                Our approach combines strategic thinking with meticulous craft, 
                ensuring every project delivers both aesthetic excellence and 
                functional performance.
              </p>
            </div>
          </div>
          
          <div className="aspect-[4/5] bg-muted overflow-hidden">
            <img
              src="https://images.unsplash.com/photo-1497366216548-37526070297c?w=600&h=750&fit=crop&crop=center"
              alt="Studio workspace"
              className="w-full h-full object-cover"
            />
          </div>
        </div>
      </div>
    </section>
  );
};

export default About;