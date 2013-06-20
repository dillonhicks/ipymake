PROJECT(MPGD)

LINK_LIBRARIES(gsched kusp pthread dsui m)

ADD_EXECUTABLE(socketpair_test socketpair_test.c)

#ADD_EXECUTABLE(tcp_test tcp_test.c)

#ADD_EXECUTABLE(tcp_server tcp_server.c)

#ADD_EXECUTABLE(tcp_client tcp_client.c)

ADD_EXECUTABLE(simple-model simple-model.c mpgd.c)
