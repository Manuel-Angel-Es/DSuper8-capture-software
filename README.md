# DSuper8-capture-software
The DSuper8 software is oriented to the digitalization of inversible films of any format. Works in combination
with a modified projector with a stepping motor for transporting the film, together with a nanocomputer and a Raspberry
Pi HQ camera.

Digitization is carried out by the frame-by-frame procedure, that is, they are taken one after the other images of
each of the frames that make up the film. These images are archived individually, each image in a different file. Later
these files are mounted with other software, for example ffmpeg, to get the final video file.

Only images are digitized. The software does not contemplate the digitization of the audio of sound films.
The system works according to the client-server model. A PC with Linux or Windows, or a Mac can be used as a
client. The Raspberry Pi acts as a server, executing commands from the client's GUI. It performs the functions of
controlling the stepper motor, lighting and capturing images that are sent via LAN to the client for processing and
archiving.

At first it was used mainly for the digitization of films in Super8 format, hence its name. DSuper8 ( Digitize
Super8), but actually the software is format independent. To digitize a determined format logically we must have a
projector compatible with the desired format and an optical system appropriate for taking images of that format.
The server software has been tested with Raspberry Pi 2, 3 and 4, with a minimum of 1 GB of RAM.

Today, virtually everyone uses the Raspberry Pi HQ camera exclusively. For this reason, support for the old V1
camera has been removed in this software version.

Once configured, the software performs the operations of capturing the images, inversion of the images,
cropping unwanted edges, image rotation, corner rounding, and image scaling to the desired final resolution. All
operations are carried out on the fly and only the final image is saved on file resulting.

It is important to note that the system does not use any type of sensor to detect the correct positioning of the
frame to be digitized. With a modified projector this device is unnecessary. Own projector mechanism correctly places
the pictures successively. Once the first frame is positioned, the system automatically tracks the position of the film and
frames are accurately digitized.

For the system to work in this way, it is essential to use a mechanically coupled stepper motor to the main shaft
of the projector. Normally, with each turn of the main axis, it advances/reverses exactly one frame. For this reason, it is
essential that the main axis faithfully follow the movements of the engine. It is recommended to make the mechanical
coupling by means of gears.
